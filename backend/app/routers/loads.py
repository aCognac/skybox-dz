from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter(prefix="/loads", tags=["loads"])


@router.get("/")
async def list_loads(db: AsyncSession = Depends(get_db)):
    """Return all loads in the database."""
    # TODO: query Load model and return results
    return []


@router.post("/")
async def create_load(db: AsyncSession = Depends(get_db)):
    """Manually create a load (Tier 3 — no scraper)."""
    # TODO: accept load data, insert, return created load
    return {}
