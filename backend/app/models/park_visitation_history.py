"""ORM model for historical park visitation observations."""

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ParkVisitationHistory(Base):
    """Monthly historical visitation metrics for each park."""

    __tablename__ = "park_visitation_history"
    __table_args__ = (UniqueConstraint("park_id", "observation_month", name="uq_history_month"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    park_id: Mapped[int] = mapped_column(ForeignKey("parks.id", ondelete="CASCADE"), nullable=False)
    observation_month: Mapped[date] = mapped_column(Date, nullable=False)
    visits: Mapped[int] = mapped_column(Integer, nullable=False)

    park = relationship("Park", back_populates="visitation_history")
