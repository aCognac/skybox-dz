from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Load(Base):
    __tablename__ = "loads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    burble_load_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    load_number: Mapped[int] = mapped_column(Integer, nullable=False)
    aircraft: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    load_master: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    departed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # cloud | local | manual
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="cloud")
    confirmed_departed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    jumpers: Mapped[list["Jumper"]] = relationship(
        "Jumper", back_populates="load", cascade="all, delete-orphan"
    )


class Jumper(Base):
    __tablename__ = "jumpers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    load_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("loads.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    group_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    formation: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    rig: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    load: Mapped["Load"] = relationship("Load", back_populates="jumpers")
