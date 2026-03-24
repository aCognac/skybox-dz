from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Load(Base):
    __tablename__ = "loads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    load_number: Mapped[str] = mapped_column(String(32), nullable=False)
    # Approximate jump-run time — used for display/sorting only
    jump_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # cloud | local | manual
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="manual")
    # JSON array of jumper names/details as returned by scraper
    raw_jumpers: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
