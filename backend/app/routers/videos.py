from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("/")
async def list_videos(db: AsyncSession = Depends(get_db)):
    """Return all discovered video files."""
    # TODO: query VideoFile model and return results
    return []


@router.post("/{video_id}/thumbnail")
async def get_thumbnail(video_id: int, lens: int = 0):
    """
    Generate and return a JPEG thumbnail for a video file.

    lens: 0 = first lens, 1 = second lens (360 formats only).
    Uses FFmpeg to extract a single frame.
    """
    # TODO: invoke FFmpeg, return StreamingResponse with JPEG
    return {"video_id": video_id, "lens": lens}
