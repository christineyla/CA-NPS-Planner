from datetime import date, timedelta

from app.models import ParkAlert, ParkVisitationForecast
from app.services.recommendations import (
    forecast_overlaps_alert,
    get_best_weeks,
    is_severe_alert,
    should_suppress_week,
)
from app.services.scoring import (
    calculate_accessibility_score,
    calculate_crowd_score,
    calculate_trip_score,
    calculate_weather_score,
    is_hidden_gem_week,
)


def _forecast(
    week_offset: int, trip_score: float, crowd_score: float = 50, weather_score: float = 70
):
    week_start = date(2026, 1, 5) + timedelta(days=week_offset * 7)
    return ParkVisitationForecast(
        park_id=1,
        week_start=week_start,
        week_end=week_start + timedelta(days=6),
        predicted_visits=20000 + week_offset * 100,
        crowd_score=crowd_score,
        weather_score=weather_score,
        accessibility_score=80,
        trip_score=trip_score,
    )


def _alert(severity: str, starts_on: date, ends_on: date, is_active: bool = True):
    return ParkAlert(
        park_id=1,
        title=f"{severity} alert",
        severity=severity,
        message="event",
        starts_on=starts_on,
        ends_on=ends_on,
        is_active=is_active,
    )


def test_crowd_score_uses_percentile_rank() -> None:
    history = [1000, 1200, 1400, 1600]

    score = calculate_crowd_score(predicted_weekly_visits=1400, historical_weekly_visits=history)

    assert score == 62.5


def test_weather_score_follows_prd_bands_and_weights() -> None:
    assert calculate_weather_score(temperature_f=70, precipitation_probability=5) == 100
    assert calculate_weather_score(temperature_f=42, precipitation_probability=35) == 65
    assert calculate_weather_score(temperature_f=95, precipitation_probability=75) == 32


def test_accessibility_score_weighting() -> None:
    score = calculate_accessibility_score(
        airport_access_score=80,
        drive_access_score=70,
        road_access_score=60,
        seasonal_access_score=50,
    )

    assert score == 70


def test_trip_score_weighting() -> None:
    score = calculate_trip_score(crowd_score=20, weather_score=80, accessibility_score=70)

    assert score == 79


def test_hidden_gem_threshold() -> None:
    assert is_hidden_gem_week(crowd_score=39.99, weather_score=60.01)
    assert not is_hidden_gem_week(crowd_score=40, weather_score=70)
    assert not is_hidden_gem_week(crowd_score=10, weather_score=60)


def test_severe_alert_detection_and_overlap() -> None:
    forecast = _forecast(week_offset=1, trip_score=70)
    severe = _alert("severe", forecast.week_start, forecast.week_end)
    low = _alert("low", forecast.week_start, forecast.week_end)

    assert is_severe_alert(severe)
    assert not is_severe_alert(low)
    assert forecast_overlaps_alert(forecast, severe)


def test_week_suppression_only_for_active_severe_overlaps() -> None:
    forecast = _forecast(week_offset=0, trip_score=78)
    severe_inactive = _alert("severe", forecast.week_start, forecast.week_end, is_active=False)
    severe_non_overlap = _alert(
        "critical", forecast.week_end + timedelta(days=2), forecast.week_end + timedelta(days=10)
    )
    severe_overlap = _alert("critical", forecast.week_start, forecast.week_end)

    assert not should_suppress_week(forecast, [severe_inactive, severe_non_overlap])
    assert should_suppress_week(forecast, [severe_overlap])


def test_best_week_ranking_applies_suppression_rules() -> None:
    f0 = _forecast(week_offset=0, trip_score=90)
    f1 = _forecast(week_offset=1, trip_score=85)
    f2 = _forecast(week_offset=2, trip_score=88)
    alerts = [
        _alert("severe", f0.week_start, f0.week_end),
        _alert("moderate", f1.week_start, f1.week_end),
    ]

    best = get_best_weeks([f0, f1, f2], alerts, limit=2)

    assert [week.trip_score for week in best] == [88, 85]
