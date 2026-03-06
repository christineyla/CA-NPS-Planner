"""Pure scoring utilities for forecast and recommendation services."""

from __future__ import annotations

from collections.abc import Sequence


def clamp_score(value: float) -> float:
    """Clamp a score to the supported 0-100 range."""

    return max(0.0, min(100.0, round(value, 2)))


def percentile_rank(value: float, history: Sequence[float]) -> float:
    """Return percentile rank (0-100) of value within a historical distribution."""

    if not history:
        return 0.0

    less_than = sum(1 for item in history if item < value)
    equal_to = sum(1 for item in history if item == value)
    percentile = ((less_than + 0.5 * equal_to) / len(history)) * 100
    return clamp_score(percentile)


def calculate_crowd_score(
    predicted_weekly_visits: int, historical_weekly_visits: Sequence[int]
) -> float:
    """Calculate crowd score from predicted visits percentile in park history."""

    return percentile_rank(
        float(predicted_weekly_visits), [float(item) for item in historical_weekly_visits]
    )


def _temperature_comfort_score(temperature_f: float) -> float:
    if 55 <= temperature_f <= 75:
        return 100.0
    if 40 <= temperature_f < 55:
        return 75.0
    if 75 < temperature_f <= 85:
        return 70.0
    if temperature_f > 90 or temperature_f < 40:
        return 40.0
    return 55.0


def _precipitation_factor(precipitation_probability: float) -> float:
    if precipitation_probability < 10:
        return 100.0
    if precipitation_probability < 30:
        return 80.0
    if precipitation_probability <= 60:
        return 50.0
    return 20.0


def calculate_weather_score(temperature_f: float, precipitation_probability: float) -> float:
    """Calculate weather score using PRD temperature and precipitation weighting."""

    temp_component = _temperature_comfort_score(temperature_f)
    precip_component = _precipitation_factor(precipitation_probability)
    return clamp_score((0.6 * temp_component) + (0.4 * precip_component))


def calculate_accessibility_score(
    airport_access_score: float,
    drive_access_score: float,
    road_access_score: float,
    seasonal_access_score: float,
) -> float:
    """Calculate weighted accessibility score from park transport factors."""

    weighted_score = (
        0.4 * airport_access_score
        + 0.3 * drive_access_score
        + 0.2 * road_access_score
        + 0.1 * seasonal_access_score
    )
    return clamp_score(weighted_score)


def calculate_trip_score(
    crowd_score: float, weather_score: float, accessibility_score: float
) -> float:
    """Calculate overall week desirability from core score components."""

    score = 0.6 * (100 - crowd_score) + 0.3 * weather_score + 0.1 * accessibility_score
    return clamp_score(score)


def is_hidden_gem_week(crowd_score: float, weather_score: float) -> bool:
    """Classify hidden gem weeks from PRD thresholds."""

    return crowd_score < 40 and weather_score > 60
