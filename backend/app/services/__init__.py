"""Service layer exports."""

from app.services.recommendations import (
    SEVERE_ALERT_LEVELS,
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
from app.services.seed_data import FORECAST_WEEKS, PARK_CONFIGS, seed_database

__all__ = [
    "FORECAST_WEEKS",
    "PARK_CONFIGS",
    "SEVERE_ALERT_LEVELS",
    "calculate_accessibility_score",
    "calculate_crowd_score",
    "calculate_trip_score",
    "calculate_weather_score",
    "forecast_overlaps_alert",
    "get_best_weeks",
    "is_hidden_gem_week",
    "is_severe_alert",
    "seed_database",
    "should_suppress_week",
]
