"""ORM model for park metadata and accessibility scores."""

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Park(Base):
    """National park metadata and accessibility scoring dimensions."""

    __tablename__ = "parks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    state: Mapped[str] = mapped_column(String(30), nullable=False, default="CA")
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    airport_access_score: Mapped[float] = mapped_column(Float, nullable=False)
    drive_access_score: Mapped[float] = mapped_column(Float, nullable=False)
    road_access_score: Mapped[float] = mapped_column(Float, nullable=False)
    seasonal_access_score: Mapped[float] = mapped_column(Float, nullable=False)
    accessibility_score: Mapped[float] = mapped_column(Float, nullable=False)

    nearest_major_airport: Mapped[str] = mapped_column(String(120), nullable=False)
    distance_to_nearest_airport_miles: Mapped[float] = mapped_column(Float, nullable=False)
    nearest_city: Mapped[str] = mapped_column(String(120), nullable=False)
    distance_from_nearest_city: Mapped[str] = mapped_column(String(120), nullable=False)
    road_access_description: Mapped[str] = mapped_column(String(280), nullable=False)
    seasonal_access_description: Mapped[str] = mapped_column(String(280), nullable=False)

    visitation_history = relationship(
        "ParkVisitationHistory",
        back_populates="park",
        cascade="all, delete-orphan",
    )
    visitation_forecast = relationship(
        "ParkVisitationForecast",
        back_populates="park",
        cascade="all, delete-orphan",
    )
    crowd_calendar_entries = relationship(
        "CrowdCalendar",
        back_populates="park",
        cascade="all, delete-orphan",
    )
    alerts = relationship("ParkAlert", back_populates="park", cascade="all, delete-orphan")
