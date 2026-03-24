from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class NormalisedJumper:
    name: str
    rig: Optional[str] = None
    discipline: Optional[str] = None


@dataclass
class NormalisedLoad:
    load_number: str
    jumpers: list[NormalisedJumper] = field(default_factory=list)
    # Approximate jump-run time — display/sort only, never used for matching
    jump_run_at: Optional[datetime] = None


class BaseScraper(ABC):
    """
    Adapter interface for manifest scrapers.

    All scrapers must return normalised Load/Jumper objects so the rest of
    the application is agnostic to the data source.

    Tier 1 (cloud):  BurbleScraper(base_url="https://burble.com")
    Tier 2 (local):  BurbleScraper(base_url="http://192.168.1.x")
    Tier 3 (manual): no scraper — user submits via POST /api/loads
    """

    @abstractmethod
    async def fetch_loads(self, for_date: date) -> list[NormalisedLoad]:
        """Fetch and return normalised loads for the given date."""
        ...
