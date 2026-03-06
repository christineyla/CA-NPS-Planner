"""Seed helpers for bootstrapping local development data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import CrowdCalendar, Park, ParkAlert, ParkVisitationForecast, ParkVisitationHistory

FORECAST_WEEKS = 26


@dataclass(frozen=True)
class ParkSeedConfig:
    """Core values used to generate deterministic mock data per park."""

    name: str
    slug: str
    latitude: float
    longitude: float
    airport_access_score: float
    drive_access_score: float
    road_access_score: float
    seasonal_access_score: float
    baseline_visits: int


PARK_CONFIGS: tuple[ParkSeedConfig, ...] = (
    ParkSeedConfig("Yosemite National Park", "yosemite", 37.8651, -119.5383, 78, 82, 70, 68, 82000),
    ParkSeedConfig("Joshua Tree National Park", "joshua-tree", 33.8734, -115.9010, 74, 80, 76, 84, 58000),
    ParkSeedConfig("Death Valley National Park", "death-valley", 36.5054, -117.0794, 66, 73, 65, 58, 39000),
    ParkSeedConfig("Sequoia National Park", "sequoia", 36.4864, -118.5658, 69, 77, 72, 70, 46000),
    ParkSeedConfig("Kings Canyon National Park", "kings-canyon", 36.8879, -118.5551, 63, 71, 68, 66, 35000),
)


def _composite_accessibility(config: ParkSeedConfig) -> float:
    return round(
        0.4 * config.airport_access_score
        + 0.3 * config.drive_access_score
        + 0.2 * config.road_access_score
        + 0.1 * config.seasonal_access_score,
        2,
    )


def _crowd_level(crowd_score: float) -> tuple[str, str]:
    if crowd_score <= 30:
        return "low", "#16A34A"
    if crowd_score <= 60:
        return "moderate", "#EAB308"
    if crowd_score <= 80:
        return "busy", "#F97316"
    return "extreme", "#DC2626"


def _park_alerts(park: Park, seed_start: date) -> list[ParkAlert]:
    return [
        ParkAlert(
            park=park,
            title="Trail maintenance advisory",
            severity="moderate",
            message="Select trails may have intermittent closures due to maintenance operations.",
            starts_on=seed_start + timedelta(days=14),
            ends_on=seed_start + timedelta(days=35),
            is_active=True,
        ),
        ParkAlert(
            park=park,
            title="Weekend parking congestion",
            severity="low",
            message="Primary parking lots are expected to fill before 10 AM on peak weekends.",
            starts_on=seed_start,
            ends_on=seed_start + timedelta(days=60),
            is_active=True,
        ),
    ]


def seed_database(session: Session, start_date: date | None = None) -> None:
    """Populate all mock records required by Task 2."""

    seed_start = start_date or date.today()
    # normalize to monday for cleaner week ranges
    seed_start = seed_start - timedelta(days=seed_start.weekday())

    for index, config in enumerate(PARK_CONFIGS):
        accessibility_score = _composite_accessibility(config)
        park = Park(
            name=config.name,
            slug=config.slug,
            state="CA",
            latitude=config.latitude,
            longitude=config.longitude,
            airport_access_score=config.airport_access_score,
            drive_access_score=config.drive_access_score,
            road_access_score=config.road_access_score,
            seasonal_access_score=config.seasonal_access_score,
            accessibility_score=accessibility_score,
        )
        session.add(park)
        session.flush()

        for month_offset in range(12):
            month_date = date(seed_start.year, seed_start.month, 1) - timedelta(days=30 * (11 - month_offset))
            visits = int(config.baseline_visits * (0.7 + 0.05 * (month_offset % 6))) + (index * 1100)
            session.add(
                ParkVisitationHistory(
                    park_id=park.id,
                    observation_month=month_date,
                    visits=visits,
                )
            )

        for week in range(FORECAST_WEEKS):
            week_start = seed_start + timedelta(days=7 * week)
            week_end = week_start + timedelta(days=6)
            predicted_visits = int(config.baseline_visits * (0.72 + 0.015 * week)) + (index * 650)
            crowd_score = min(100.0, round(28 + ((week * 2.3) % 65) + (index * 2.1), 2))
            weather_score = max(35.0, round(82 - abs(12 - week) * 2.1 - index * 1.5, 2))
            trip_score = round(
                0.6 * (100 - crowd_score) + 0.3 * weather_score + 0.1 * accessibility_score,
                2,
            )

            forecast = ParkVisitationForecast(
                park_id=park.id,
                week_start=week_start,
                week_end=week_end,
                predicted_visits=predicted_visits,
                crowd_score=crowd_score,
                weather_score=weather_score,
                accessibility_score=accessibility_score,
                trip_score=trip_score,
            )
            session.add(forecast)
            session.flush()

            level, color = _crowd_level(crowd_score)
            session.add(
                CrowdCalendar(
                    park_id=park.id,
                    forecast_id=forecast.id,
                    crowd_level=level,
                    color_hex=color,
                    crowd_score=crowd_score,
                )
            )

        session.add_all(_park_alerts(park=park, seed_start=seed_start))

    session.commit()
