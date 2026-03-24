from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class NormalisedJumper:
    name: str
    type: Optional[str] = None
    group_name: Optional[str] = None
    formation: Optional[str] = None
    rig: Optional[str] = None


@dataclass
class NormalisedLoad:
    burble_load_id: str
    load_number: int
    aircraft: str
    date: str           # YYYY-MM-DD
    confirmed_departed: bool
    jumpers: list[NormalisedJumper] = field(default_factory=list)
    load_master: Optional[str] = None


class BaseScraper(ABC):
    """
    Adapter interface for manifest scrapers.

    All scrapers must return normalised Load/Jumper objects so the rest of
    the application is agnostic to the data source.

    Tier 1 (cloud):  BurbleScraper(dz_id="...", base_url="https://dzm.burblesoft.eu")
    Tier 2 (local):  BurbleScraper(dz_id="...", base_url="http://192.168.1.x")
    Tier 3 (manual): no scraper — user submits via POST /api/loads
    """

    @abstractmethod
    async def fetch_loads(self, for_date: date) -> list[NormalisedLoad]:
        """Fetch and return normalised loads for the given date."""
        ...
