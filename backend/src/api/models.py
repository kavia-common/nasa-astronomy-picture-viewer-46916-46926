from __future__ import annotations

from datetime import datetime
from sqlalchemy import Date, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.api.db import Base


class APODCache(Base):
    """
    SQLAlchemy model representing a cached APOD item for a given date and hd flag.
    """
    __tablename__ = "apod_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped["date"] = mapped_column(Date, index=True)  # type: ignore[name-defined]
    hd: Mapped[int] = mapped_column(Integer, default=0)  # 0=False, 1=True
    title: Mapped[str] = mapped_column(String, nullable=False)
    explanation: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    hdurl: Mapped[str | None] = mapped_column(String, nullable=True)
    media_type: Mapped[str] = mapped_column(String, nullable=False, default="image")
    service_version: Mapped[str | None] = mapped_column(String, nullable=True)
    copyright: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("date", "hd", name="uq_apod_date_hd"),
    )
