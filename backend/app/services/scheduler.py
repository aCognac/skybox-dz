import asyncio
import logging
import time
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.load import Jumper, Load
from app.scrapers.base import NormalisedLoad
from app.scrapers.burble import BurbleScraper

logger = logging.getLogger(__name__)

# ── schedule constants (mirrors scraper.js) ───────────────────────────────────
ACTIVE_S = 30           # 30 s  — daytime
NIGHT_S = 30 * 60       # 30 min — quiet night
BOOST_S = 30            # 30 s  — night-boost after finding a load
BOOST_TTL_S = 30 * 60   # keep boost 30 min after last activity

_scraper = BurbleScraper(dz_id=settings.dz_id, base_url=settings.burble_base_url)
_task: asyncio.Task | None = None
_last_activity_at: float = 0.0


# ── solar window ──────────────────────────────────────────────────────────────

def _solar_window() -> tuple[int, int]:
    """Return (sunrise_min, sunset_min) as local minutes-since-midnight."""
    try:
        from astral import LocationInfo
        from astral.sun import sun as astral_sun

        loc = LocationInfo(
            latitude=settings.dz_lat,
            longitude=settings.dz_lon,
            timezone=settings.dz_tz,
        )
        s = astral_sun(loc.observer, date=date.today(), tzinfo=loc.timezone)

        def _to_min(dt: datetime) -> int:
            local = dt.astimezone(ZoneInfo(settings.dz_tz))
            return local.hour * 60 + local.minute

        return _to_min(s["sunrise"]), _to_min(s["sunset"])
    except Exception as exc:
        logger.debug("Solar window calculation failed (%s) — using 06:00–20:00", exc)
        return 6 * 60, 20 * 60


def _is_daytime() -> bool:
    tz = ZoneInfo(settings.dz_tz)
    now = datetime.now(tz)
    now_min = now.hour * 60 + now.minute
    sunrise_min, sunset_min = _solar_window()
    return sunrise_min <= now_min < sunset_min


def _next_interval(found_activity: bool) -> float:
    global _last_activity_at
    if found_activity:
        _last_activity_at = time.monotonic()
    if _is_daytime():
        return ACTIVE_S
    boosted = (time.monotonic() - _last_activity_at) < BOOST_TTL_S
    return BOOST_S if boosted else NIGHT_S


def _mode_label() -> str:
    if _is_daytime():
        return "daytime"
    if (time.monotonic() - _last_activity_at) < BOOST_TTL_S:
        return "night-boost"
    return "night"


# ── database upsert ───────────────────────────────────────────────────────────

async def _upsert_load(load: NormalisedLoad) -> tuple[bool, bool]:
    """
    Insert load + jumpers if not already present; upgrade confirmed_departed if needed.
    Returns (inserted, upgraded).
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Load).where(Load.burble_load_id == load.burble_load_id)
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            if load.confirmed_departed and not existing.confirmed_departed:
                existing.confirmed_departed = True
                await session.commit()
                return False, True
            return False, False

        new_load = Load(
            burble_load_id=load.burble_load_id,
            load_number=load.load_number,
            aircraft=load.aircraft,
            load_master=load.load_master,
            date=date.fromisoformat(load.date),
            departed_at=datetime.now(tz=timezone.utc),
            source="cloud",
            confirmed_departed=load.confirmed_departed,
        )
        session.add(new_load)
        await session.flush()

        for j in load.jumpers:
            session.add(
                Jumper(
                    load_id=new_load.id,
                    name=j.name,
                    type=j.type,
                    group_name=j.group_name,
                    formation=j.formation,
                    rig=j.rig,
                )
            )

        await session.commit()
        return True, False


# ── poll ──────────────────────────────────────────────────────────────────────

async def _poll_burble() -> bool:
    """Fetch loads, upsert into DB. Returns True if anything changed."""
    logger.debug("Polling Burble (dz_id=%s)", settings.dz_id)
    try:
        loads = await _scraper.fetch_loads(for_date=date.today())
    except Exception as exc:
        logger.error("Burble poll failed: %s", exc)
        return False

    saved = upgraded = 0
    for load in loads:
        inserted, upg = await _upsert_load(load)
        if inserted:
            saved += 1
            label = "departed" if load.confirmed_departed else "slots≤0 (unconfirmed)"
            logger.info(
                "Saved load #%d (%s) [%s] – %d jumpers",
                load.load_number, load.aircraft, label, len(load.jumpers),
            )
        if upg:
            upgraded += 1
            logger.info(
                "Confirmed load #%d (%s) — was unconfirmed",
                load.load_number, load.aircraft,
            )

    if loads and saved == 0 and upgraded == 0:
        logger.debug("%d load(s) already in DB", len(loads))
    elif not loads:
        logger.debug("No captured loads visible")

    return saved > 0 or upgraded > 0


# ── scheduler loop ────────────────────────────────────────────────────────────

async def _poll_loop() -> None:
    while True:
        found = await _poll_burble()
        delay = _next_interval(found)
        logger.info(
            "Next Burble poll in %.1f min (%s, tz: %s)",
            delay / 60, _mode_label(), settings.dz_tz,
        )
        await asyncio.sleep(delay)


def start_scheduler() -> None:
    global _task
    sunrise_min, sunset_min = _solar_window()
    fmt = lambda m: f"{m // 60:02d}:{m % 60:02d}"
    logger.info(
        "Scheduler starting for DZ %s (tz: %s, lat: %.2f, lon: %.2f) | "
        "solar window: %s – %s | daytime every %ds | night %dmin",
        settings.dz_id, settings.dz_tz, settings.dz_lat, settings.dz_lon,
        fmt(sunrise_min), fmt(sunset_min),
        ACTIVE_S, NIGHT_S // 60,
    )
    _task = asyncio.get_event_loop().create_task(_poll_loop())


def stop_scheduler() -> None:
    global _task
    if _task and not _task.done():
        _task.cancel()
        _task = None
