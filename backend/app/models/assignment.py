from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_file_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("video_files.id"), nullable=False
    )
    load_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("loads.id"), nullable=False
    )
    # JSON array of jumper name strings selected by user
    jumper_names: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    video_file = relationship("VideoFile")
    load = relationship("Load")
