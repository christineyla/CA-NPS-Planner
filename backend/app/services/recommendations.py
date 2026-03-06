"""Recommendation logic for best-week ranking and alert suppression."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from app.models import ParkAlert, ParkVisitationForecast

SEVERE_ALERT_LEVELS: frozenset[str] = frozenset({"red"})


def is_severe_alert(alert: ParkAlert) -> bool:
    """Return whether an alert should suppress recommendation weeks."""

    return alert.is_active and alert.severity.lower() in SEVERE_ALERT_LEVELS


def forecast_overlaps_alert(forecast: ParkVisitationForecast, alert: ParkAlert) -> bool:
    """Return true when a forecast week intersects the alert active date window."""

    return forecast.week_start <= alert.ends_on and forecast.week_end >= alert.starts_on


def should_suppress_week(forecast: ParkVisitationForecast, alerts: Sequence[ParkAlert]) -> bool:
    """Apply suppression rules for severe active alerts."""

    for alert in alerts:
        if is_severe_alert(alert) and forecast_overlaps_alert(forecast, alert):
            return True
    return False


def get_best_weeks(
    forecasts: Sequence[ParkVisitationForecast],
    alerts: Sequence[ParkAlert],
    *,
    limit: int = 5,
    min_week_start: date | None = None,
) -> list[ParkVisitationForecast]:
    """Return top ranked forecast weeks after applying suppression rules."""

    eligible = [
        forecast
        for forecast in forecasts
        if (min_week_start is None or forecast.week_start >= min_week_start)
        and not should_suppress_week(forecast, alerts)
    ]

    ranked = sorted(eligible, key=lambda row: (-row.trip_score, row.week_start))
    return ranked[:limit]
