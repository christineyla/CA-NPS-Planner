"""Query helpers for park-related API responses."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import CrowdCalendar, Park, ParkAlert, ParkVisitationForecast
from app.services.recommendations import get_best_weeks as rank_best_weeks
from app.services.scoring import is_hidden_gem_week


def get_parks(session: Session) -> Sequence[Park]:
    """Return all parks ordered alphabetically."""

    return session.scalars(select(Park).order_by(Park.name)).all()


def get_park_or_none(session: Session, park_id: int) -> Park | None:
    """Return a single park by id when present."""

    return session.scalar(select(Park).where(Park.id == park_id))


def _forecast_base_query(park_id: int) -> Select[tuple[ParkVisitationForecast]]:
    return select(ParkVisitationForecast).where(ParkVisitationForecast.park_id == park_id)


def get_park_forecast(session: Session, park_id: int) -> Sequence[ParkVisitationForecast]:
    """Return all forecast weeks for a park ordered by week start."""

    query = _forecast_base_query(park_id).order_by(ParkVisitationForecast.week_start)
    return session.scalars(query).all()


def get_latest_forecast_for_parks(
    session: Session,
) -> dict[int, ParkVisitationForecast]:
    """Return each park's earliest forecast week for map/list rollups."""

    forecasts = session.scalars(
        select(ParkVisitationForecast).order_by(ParkVisitationForecast.week_start)
    ).all()
    first_by_park: dict[int, ParkVisitationForecast] = {}
    for forecast in forecasts:
        first_by_park.setdefault(forecast.park_id, forecast)
    return first_by_park


def get_best_weeks(
    session: Session,
    park_id: int,
    *,
    limit: int = 5,
) -> Sequence[ParkVisitationForecast]:
    """Return top recommended weeks sorted by trip score descending."""

    forecasts = get_park_forecast(session, park_id)
    alerts = get_alerts(session, park_id)
    return rank_best_weeks(forecasts, alerts, limit=limit)


def get_hidden_gem_weeks(session: Session, park_id: int) -> Sequence[ParkVisitationForecast]:
    """Return weeks that satisfy hidden gem criteria from product spec."""

    forecasts = get_park_forecast(session, park_id)
    return sorted(
        [week for week in forecasts if is_hidden_gem_week(week.crowd_score, week.weather_score)],
        key=lambda row: (-row.trip_score, row.week_start),
    )


def get_crowd_calendar(session: Session, park_id: int) -> Sequence[CrowdCalendar]:
    """Return calendar rows for a park ordered by forecast week."""

    query = (
        select(CrowdCalendar)
        .join(ParkVisitationForecast, CrowdCalendar.forecast_id == ParkVisitationForecast.id)
        .where(CrowdCalendar.park_id == park_id)
        .order_by(ParkVisitationForecast.week_start)
    )
    return session.scalars(query).all()


def get_alerts(session: Session, park_id: int) -> Sequence[ParkAlert]:
    """Return all alerts for a park sorted by start date."""

    query = select(ParkAlert).where(ParkAlert.park_id == park_id).order_by(ParkAlert.starts_on)
    return session.scalars(query).all()
