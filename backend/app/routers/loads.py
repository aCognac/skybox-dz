from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.load import Jumper, Load

router = APIRouter(prefix="/loads", tags=["loads"])


# ── response schemas ──────────────────────────────────────────────────────────

class JumperOut(BaseModel):
    id: int
    name: str
    type: Optional[str]
    group_name: Optional[str]
    formation: Optional[str]
    rig: Optional[str]

    model_config = {"from_attributes": True}


class LoadOut(BaseModel):
    id: int
    burble_load_id: str
    load_number: int
    aircraft: str
    load_master: Optional[str]
    date: date
    source: str
    confirmed_departed: bool
    jumpers: list[JumperOut] = []

    model_config = {"from_attributes": True}


# ── request schema (manual / Tier 3) ─────────────────────────────────────────

class JumperIn(BaseModel):
    name: str
    type: Optional[str] = None
    group_name: Optional[str] = None
    formation: Optional[str] = None
    rig: Optional[str] = None


class LoadIn(BaseModel):
    load_number: int
    aircraft: str = ""
    load_master: Optional[str] = None
    date: date
    jumpers: list[JumperIn] = []


# ── routes ────────────────────────────────────────────────────────────────────

@router.get("/dates", response_model=list[date])
async def list_dates(db: AsyncSession = Depends(get_db)):
    """List distinct dates that have recorded loads, newest first."""
    result = await db.execute(
        select(Load.date).distinct().order_by(Load.date.desc())
    )
    return [row[0] for row in result.all()]


@router.get("/", response_model=list[LoadOut])
async def list_loads(
    date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    """Return loads, optionally filtered by date. Defaults to today."""
    filter_date = date or __import__("datetime").date.today()
    result = await db.execute(
        select(Load)
        .where(Load.date == filter_date)
        .options(selectinload(Load.jumpers))
        .order_by(Load.load_number)
    )
    loads = result.scalars().all()
    return [LoadOut.model_validate(l) for l in loads]


@router.get("/{load_id}", response_model=LoadOut)
async def get_load(load_id: int, db: AsyncSession = Depends(get_db)):
    """Return a single load with its full jumper list."""
    result = await db.execute(
        select(Load)
        .where(Load.id == load_id)
        .options(selectinload(Load.jumpers))
    )
    load = result.scalar_one_or_none()
    if not load:
        raise HTTPException(status_code=404, detail="Load not found")
    return LoadOut.model_validate(load)


@router.post("/", response_model=LoadOut, status_code=201)
async def create_load(body: LoadIn, db: AsyncSession = Depends(get_db)):
    """Manually create a load (Tier 3 — no scraper)."""
    burble_load_id = f"manual-{body.date}-{body.load_number}"
    new_load = Load(
        burble_load_id=burble_load_id,
        load_number=body.load_number,
        aircraft=body.aircraft,
        load_master=body.load_master,
        date=body.date,
        departed_at=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
        source="manual",
        confirmed_departed=True,
    )
    db.add(new_load)
    await db.flush()
    for j in body.jumpers:
        db.add(Jumper(load_id=new_load.id, **j.model_dump()))
    await db.commit()
    await db.refresh(new_load)
    result = await db.execute(
        select(Load)
        .where(Load.id == new_load.id)
        .options(selectinload(Load.jumpers))
    )
    return LoadOut.model_validate(result.scalar_one())
