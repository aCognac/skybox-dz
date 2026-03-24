from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VideoFile(Base):
    __tablename__ = "video_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Absolute path on VIDEO_STORAGE_PATH volume
    file_path: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    # insv | 360 | mp4
    format: Mapped[str] = mapped_column(String(8), nullable=False)
    # 1 for standard, 2 for dual-lens 360 formats
    lens_count: Mapped[int] = mapped_column(Integer, default=1)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # File mtime — used for sorting only, never for jumper matching
    file_mtime: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
