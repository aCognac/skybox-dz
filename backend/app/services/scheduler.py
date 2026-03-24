import logging
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.scrapers.burble import BurbleScraper

logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler()
_scraper = BurbleScraper(base_url=settings.burble_base_url)


async def _poll_burble() -> None:
    """APScheduler job: fetch today's loads from Burble and upsert into DB."""
    logger.info("Polling Burble at %s", settings.burble_base_url)
    try:
        loads = await _scraper.fetch_loads(for_date=date.today())
        # TODO: upsert loads into database
        logger.info("Fetched %d loads", len(loads))
    except NotImplementedError:
        logger.warning("Burble scraper not yet implemented — skipping poll")
    except Exception as exc:
        logger.error("Burble poll failed: %s", exc)


def start_scheduler() -> None:
    _scheduler.add_job(
        _poll_burble,
        "interval",
        minutes=settings.burble_poll_interval_minutes,
        id="burble_poll",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "Scheduler started — Burble poll every %d min",
        settings.burble_poll_interval_minutes,
    )


def stop_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
