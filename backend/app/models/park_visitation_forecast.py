"""ORM model for weekly visitation forecasts and scores."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ParkVisitationForecast(Base):
    """Weekly forecast projections and score outputs for each park."""

    __tablename__ = "park_visitation_forecast"
    __table_args__ = (UniqueConstraint("park_id", "week_start", name="uq_forecast_week"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    park_id: Mapped[int] = mapped_column(ForeignKey("parks.id", ondelete="CASCADE"), nullable=False)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_visits: Mapped[int] = mapped_column(Integer, nullable=False)
    crowd_score: Mapped[float] = mapped_column(Float, nullable=False)
    weather_score: Mapped[float] = mapped_column(Float, nullable=False)
    accessibility_score: Mapped[float] = mapped_column(Float, nullable=False)
    trip_score: Mapped[float] = mapped_column(Float, nullable=False)
    forecast_generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    model_trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_cutoff_date: Mapped[date] = mapped_column(Date, nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)

    park = relationship("Park", back_populates="visitation_forecast")
    crowd_calendar_entry = relationship(
        "CrowdCalendar",
        back_populates="forecast",
        uselist=False,
        cascade="all, delete-orphan",
    )
