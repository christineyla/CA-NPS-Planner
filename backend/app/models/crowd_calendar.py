"""ORM model for color-coded crowd calendar entries."""

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CrowdCalendar(Base):
    """Weekly crowd calendar rows tied to forecast records."""

    __tablename__ = "crowd_calendar"
    __table_args__ = (UniqueConstraint("park_id", "forecast_id", name="uq_calendar_forecast"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    park_id: Mapped[int] = mapped_column(ForeignKey("parks.id", ondelete="CASCADE"), nullable=False)
    forecast_id: Mapped[int] = mapped_column(
        ForeignKey("park_visitation_forecast.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    crowd_level: Mapped[str] = mapped_column(String(20), nullable=False)
    color_hex: Mapped[str] = mapped_column(String(7), nullable=False)
    crowd_score: Mapped[float] = mapped_column(Float, nullable=False)

    park = relationship("Park", back_populates="crowd_calendar_entries")
    forecast = relationship("ParkVisitationForecast", back_populates="crowd_calendar_entry")
