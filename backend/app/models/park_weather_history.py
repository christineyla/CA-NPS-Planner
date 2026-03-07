"""ORM model for daily historical weather observations per park."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ParkWeatherHistory(Base):
    """Daily weather observations for each park used in weather scoring and forecasting."""

    __tablename__ = "park_weather_history"
    __table_args__ = (UniqueConstraint("park_id", "observation_date", name="uq_weather_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    park_id: Mapped[int] = mapped_column(ForeignKey("parks.id", ondelete="CASCADE"), nullable=False)
    observation_date: Mapped[date] = mapped_column(Date, nullable=False)
    avg_temp_f: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_temp_f: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_temp_f: Mapped[float | None] = mapped_column(Float, nullable=True)
    precipitation_mm: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    data_source: Mapped[str] = mapped_column(String(140), nullable=False)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    park = relationship("Park", back_populates="weather_history")
