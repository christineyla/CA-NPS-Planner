"""ORM model for historical Google Trends search-interest observations."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ParkTrendHistory(Base):
    """Historical trend index records for in-scope parks."""

    __tablename__ = "park_trend_history"
    __table_args__ = (UniqueConstraint("park_id", "observation_date", name="uq_trend_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    park_id: Mapped[int] = mapped_column(ForeignKey("parks.id", ondelete="CASCADE"), nullable=False)
    observation_date: Mapped[date] = mapped_column(Date, nullable=False)
    google_trends_index: Mapped[float] = mapped_column(Float, nullable=False)
    data_source: Mapped[str] = mapped_column(String(140), nullable=False)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    park = relationship("Park", back_populates="trend_history")
