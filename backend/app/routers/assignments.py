from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.get("/")
async def list_assignments(db: AsyncSession = Depends(get_db)):
    """Return all assignments."""
    # TODO: query Assignment model
    return []


@router.post("/")
async def create_assignment(db: AsyncSession = Depends(get_db)):
    """
    Assign a video group to a load with selected jumpers.

    Flow: user selects video group → selects load → selects jumpers filmed.
    """
    # TODO: accept AssignmentCreate schema, insert, return created assignment
    return {}


@router.delete("/{assignment_id}")
async def delete_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an assignment."""
    # TODO: delete and return 204
    return {}
