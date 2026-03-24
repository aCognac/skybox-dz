import logging
from datetime import date, datetime, timezone
from typing import Optional

import httpx

from app.scrapers.base import BaseScraper, NormalisedJumper, NormalisedLoad

logger = logging.getLogger(__name__)

_BASE_URL = "https://dzm.burblesoft.eu"
_API_URL = "https://eu-displays.burblesoft.eu/ajax_dzm2_frontend_jumpermanifestpublic"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Cache-Control": "no-cache",
}


class BurbleScraper(BaseScraper):
    """
    Scraper for Burble manifest system (eu-displays endpoint).

    Mirrors the logic from the proven scraper.js implementation:
    - Pre-flight GET to acquire session cookie
    - POST to ajax_dzm2_frontend_jumpermanifestpublic
    - Classify loads as confirmed (status=="departed") or unconfirmed (slots<=0)
    - Parse jumpers from nested groups array

    Works for both Tier 1 (cloud) and Tier 2 (local DZ wifi) by configuring
    base_url via the BURBLE_BASE_URL environment variable.
    """

    def __init__(self, dz_id: str, base_url: str = _BASE_URL) -> None:
        self.dz_id = dz_id
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    def _make_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers=_HEADERS,
        )

    @property
    def _http(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = self._make_client()
        return self._client

    def _reset_client(self) -> None:
        self._client = None

    async def fetch_loads(self, for_date: date) -> list[NormalisedLoad]:
        page_url = f"{self.base_url}/jmp?dz_id={self.dz_id}"
        try:
            # Pre-flight: visit the public manifest page so Burble sets session cookies.
            await self._http.get(page_url)

            params = {
                "action": "getLoads",
                "dz_id": self.dz_id,
                "aircraft": "0",
                "columns": "4",
                "display_tandem": "1",
                "display_student": "1",
                "display_sport": "1",
                "display_menu": "1",
                "font_size": "0",
                "date_format": "d/m/Y",
                "acl_application": "Burble DZM",
            }
            resp = await self._http.post(
                _API_URL,
                data=params,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": "https://eu-displays.burblesoft.eu/jmp",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "X-Requested-With": "XMLHttpRequest",
                },
            )
            data = resp.json()
            if not data.get("success") or not isinstance(data.get("loads"), list):
                logger.error("Unexpected Burble API response: %s", str(data)[:300])
                return []
            api_loads = data["loads"]
        except Exception as exc:
            logger.error("Burble fetch failed: %s", exc)
            self._reset_client()
            return []

        today = for_date.isoformat()
        now = datetime.now(tz=timezone.utc)
        result: list[NormalisedLoad] = []

        for load_obj in api_loads:
            kind = self._classify_load(load_obj)
            if not kind:
                continue

            burble_load_id = str(load_obj.get("id", ""))
            name_str = load_obj.get("name") or ""
            name_parts = name_str.split(" ")
            last = name_parts[-1] if name_parts else ""
            load_number = int(last) if last.isdigit() else 0
            aircraft = (
                load_obj.get("aircraft_name")
                or " ".join(name_parts[:-1])
                or ""
            )

            lm = load_obj.get("lm")
            if isinstance(lm, str):
                load_master = lm or None
            elif isinstance(lm, dict):
                load_master = lm.get("name") or lm.get("display_name") or None
            else:
                load_master = None

            jumpers = self._parse_jumpers(load_obj)

            result.append(
                NormalisedLoad(
                    burble_load_id=burble_load_id,
                    load_number=load_number,
                    aircraft=aircraft,
                    load_master=load_master,
                    date=today,
                    confirmed_departed=(kind == "confirmed"),
                    jumpers=jumpers,
                )
            )

        return result

    # ── classification ────────────────────────────────────────────────────────

    def _classify_load(self, load_obj: dict) -> Optional[str]:
        """
        Returns "confirmed", "unconfirmed", or None (still boarding).

        Mirrors classifyLoad() in scraper.js:
        - "departed" status string → confirmed
        - numeric status ≤ 0      → unconfirmed
        - open_slots / slots ≤ 0  → unconfirmed
        """
        status_str = str(load_obj.get("status") or "").strip()
        if status_str.lower() == "departed":
            return "confirmed"

        if status_str:
            try:
                if float(status_str) <= 0:
                    return "unconfirmed"
            except ValueError:
                pass

        open_slots = load_obj.get("open_slots")
        if open_slots is None:
            slots = load_obj.get("slots")
            if isinstance(slots, (int, float)):
                open_slots = slots

        if isinstance(open_slots, (int, float)) and open_slots <= 0:
            return "unconfirmed"

        return None

    # ── jumper parsing ────────────────────────────────────────────────────────

    def _parse_jumpers(self, load_obj: dict) -> list[NormalisedJumper]:
        """
        Extract flat jumper list from load_obj.groups (array of arrays).

        Mirrors parseJumpers() in scraper.js.
        """
        jumpers: list[NormalisedJumper] = []
        groups = load_obj.get("groups")
        if not isinstance(groups, list):
            return jumpers
        for group in groups:
            slots = group if isinstance(group, list) else [group]
            for slot in slots:
                if not isinstance(slot, dict):
                    continue
                name = slot.get("name") or ""
                if not name:
                    continue
                jumpers.append(
                    NormalisedJumper(
                        name=name,
                        type=slot.get("type"),
                        group_name=slot.get("team_name"),
                        formation=slot.get("jump") or slot.get("formation_type_name"),
                        rig=slot.get("rig_name"),
                    )
                )
        return jumpers
