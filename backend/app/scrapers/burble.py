from datetime import date

import httpx

from app.scrapers.base import BaseScraper, NormalisedJumper, NormalisedLoad


class BurbleScraper(BaseScraper):
    """
    Scraper for Burble manifest system.

    Works for both Tier 1 (cloud) and Tier 2 (local DZ wifi) by configuring
    base_url via the BURBLE_BASE_URL environment variable.
    """

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def fetch_loads(self, for_date: date) -> list[NormalisedLoad]:
        """
        Fetch loads from Burble for the given date.

        TODO: implement actual Burble API/scraping logic.
        """
        async with httpx.AsyncClient(timeout=10) as client:  # noqa: F841
            # TODO: call Burble endpoint and parse response
            raise NotImplementedError("Burble scraper not yet implemented")

    def _parse_jumper(self, raw: dict) -> NormalisedJumper:
        """Convert a raw Burble jumper dict to a NormalisedJumper."""
        return NormalisedJumper(
            name=raw.get("name", ""),
            rig=raw.get("rig"),
            discipline=raw.get("discipline"),
        )
