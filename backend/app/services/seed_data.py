"""Seed helpers for bootstrapping local development data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.models import CrowdCalendar, Park, ParkAlert, ParkVisitationForecast, ParkVisitationHistory
from app.services.scoring import (
    calculate_accessibility_score,
    calculate_crowd_score,
    calculate_trip_score,
    calculate_weather_score,
)

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
    nearest_major_airport: str
    distance_to_nearest_airport_miles: float
    nearest_city: str
    distance_from_nearest_city: str
    road_access_description: str
    seasonal_access_description: str
    baseline_visits: int


PARK_CONFIGS: tuple[ParkSeedConfig, ...] = (
    ParkSeedConfig(
        "Yosemite National Park",
        "yosemite",
        37.8651,
        -119.5383,
        78,
        82,
        70,
        68,
        "Fresno Yosemite International Airport (FAT)",
        95,
        "Fresno, CA",
        "65 miles / ~1 hr 30 min drive",
        "Primary access via CA-41, CA-120, and CA-140; winding mountain roads can slow travel.",
        "Tioga Road and Glacier Point Road typically close seasonally due to snow.",
        82000,
    ),
    ParkSeedConfig(
        "Joshua Tree National Park",
        "joshua-tree",
        33.8734,
        -115.9010,
        74,
        80,
        76,
        84,
        "Palm Springs International Airport (PSP)",
        40,
        "Palm Springs, CA",
        "38 miles / ~50 min drive",
        "Paved highway access from multiple entrances with straightforward desert driving routes.",
        (
            "Generally open year-round, though extreme summer heat can limit "
            "comfortable daytime access."
        ),
        58000,
    ),
    ParkSeedConfig(
        "Death Valley National Park",
        "death-valley",
        36.5054,
        -117.0794,
        66,
        73,
        65,
        58,
        "Harry Reid International Airport (LAS)",
        120,
        "Pahrump, NV",
        "62 miles / ~1 hr 20 min drive",
        "Long approach roads with limited services; fuel and water planning is essential.",
        (
            "Year-round access with periodic closures after flooding and hazardous "
            "summer heat windows."
        ),
        39000,
    ),
    ParkSeedConfig(
        "Sequoia National Park",
        "sequoia",
        36.4864,
        -118.5658,
        69,
        77,
        72,
        70,
        "Fresno Yosemite International Airport (FAT)",
        84,
        "Visalia, CA",
        "36 miles / ~1 hr drive",
        "Access roads climb rapidly in elevation with frequent curves and slower mountain travel.",
        "Higher-elevation roads may require chains or temporary winter restrictions.",
        46000,
    ),
    ParkSeedConfig(
        "Kings Canyon National Park",
        "kings-canyon",
        36.8879,
        -118.5551,
        63,
        71,
        68,
        66,
        "Fresno Yosemite International Airport (FAT)",
        85,
        "Fresno, CA",
        "82 miles / ~1 hr 50 min drive",
        "Single primary approach corridor into canyon areas with limited alternate routing.",
        "Cedar Grove and some high-country roads have predictable seasonal closures.",
        35000,
    ),
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
    alerts_by_slug: dict[str, list[dict[str, str | int | bool]]] = {
        "yosemite": [
            {
                "title": "El Portal Road rockslide closure",
                "severity": "red",
                "message": (
                    "A major rockslide has closed a key Valley approach route. "
                    "Expect detours and extended drive times."
                ),
                "start_offset_days": 7,
                "end_offset_days": 28,
                "is_active": True,
            },
            {
                "title": "Merced River flooding watch",
                "severity": "orange",
                "message": (
                    "High runoff may temporarily close low-elevation trails, "
                    "shuttle stops, and river access points."
                ),
                "start_offset_days": 35,
                "end_offset_days": 49,
                "is_active": True,
            },
            {
                "title": "Half Dome cables weather caution",
                "severity": "yellow",
                "message": (
                    "Afternoon storms are expected; rangers advise early starts "
                    "and flexible summit plans."
                ),
                "start_offset_days": 56,
                "end_offset_days": 70,
                "is_active": True,
            },
        ],
        "joshua-tree": [
            {
                "title": "Extreme heat advisory",
                "severity": "red",
                "message": (
                    "Daytime highs above 110°F create dangerous exposure risk; "
                    "avoid midday hiking and climbing."
                ),
                "start_offset_days": 14,
                "end_offset_days": 35,
                "is_active": True,
            },
            {
                "title": "Cottonwood area flash flooding",
                "severity": "orange",
                "message": (
                    "Monsoonal storms may produce washouts and short-notice "
                    "closures on backcountry roads."
                ),
                "start_offset_days": 42,
                "end_offset_days": 56,
                "is_active": True,
            },
            {
                "title": "Ryan Campground water system repairs",
                "severity": "yellow",
                "message": (
                    "Intermittent utility interruptions are expected while "
                    "maintenance crews complete repairs."
                ),
                "start_offset_days": 0,
                "end_offset_days": 21,
                "is_active": True,
            },
        ],
        "death-valley": [
            {
                "title": "Heat danger and area closure",
                "severity": "red",
                "message": (
                    "Sections of exposed salt pan viewpoints are closed during "
                    "prolonged extreme heat conditions."
                ),
                "start_offset_days": 0,
                "end_offset_days": 42,
                "is_active": True,
            },
            {
                "title": "CA-190 storm damage major closure",
                "severity": "red",
                "message": (
                    "A major road segment remains closed for reconstruction " "after flood damage."
                ),
                "start_offset_days": 49,
                "end_offset_days": 77,
                "is_active": True,
            },
            {
                "title": "Windblown dust visibility caution",
                "severity": "yellow",
                "message": (
                    "Strong crosswinds can reduce visibility and affect "
                    "high-profile vehicles on open roads."
                ),
                "start_offset_days": 21,
                "end_offset_days": 35,
                "is_active": True,
            },
        ],
        "sequoia": [
            {
                "title": "Generals Highway wildfire operations",
                "severity": "orange",
                "message": (
                    "Active wildfire response may trigger rolling one-lane "
                    "controls and smoke impacts."
                ),
                "start_offset_days": 7,
                "end_offset_days": 30,
                "is_active": True,
            },
            {
                "title": "Foothills prescribed burn advisory",
                "severity": "yellow",
                "message": (
                    "Smoke-sensitive visitors should plan around scheduled "
                    "burn windows and shifting wind patterns."
                ),
                "start_offset_days": 31,
                "end_offset_days": 45,
                "is_active": True,
            },
            {
                "title": "Mineral King Road overnight closure",
                "severity": "orange",
                "message": (
                    "Nighttime paving operations close access from 8 PM to 6 AM " "on weekdays."
                ),
                "start_offset_days": 46,
                "end_offset_days": 67,
                "is_active": True,
            },
        ],
        "kings-canyon": [
            {
                "title": "Cedar Grove area closure",
                "severity": "red",
                "message": (
                    "Rockfall risk has closed Cedar Grove roads and trails until "
                    "slope stabilization is complete."
                ),
                "start_offset_days": 14,
                "end_offset_days": 49,
                "is_active": True,
            },
            {
                "title": "South Fork Kings River flooding",
                "severity": "orange",
                "message": (
                    "Localized flooding may impact low-water crossings and "
                    "selected canyon trailheads."
                ),
                "start_offset_days": 56,
                "end_offset_days": 70,
                "is_active": True,
            },
            {
                "title": "High-elevation weather caution",
                "severity": "yellow",
                "message": (
                    "Late-season snow and cold nights may require traction "
                    "devices on selected routes."
                ),
                "start_offset_days": 0,
                "end_offset_days": 18,
                "is_active": True,
            },
        ],
    }

    park_alert_specs = alerts_by_slug[park.slug]
    return [
        ParkAlert(
            park=park,
            title=spec["title"],
            severity=spec["severity"],
            message=spec["message"],
            starts_on=seed_start + timedelta(days=int(spec["start_offset_days"])),
            ends_on=seed_start + timedelta(days=int(spec["end_offset_days"])),
            is_active=bool(spec["is_active"]),
        )
        for spec in park_alert_specs
    ]


def seed_database(session: Session, start_date: date | None = None) -> None:
    """Populate all mock records required by Task 2."""

    seed_start = start_date or date.today()
    # normalize to monday for cleaner week ranges
    seed_start = seed_start - timedelta(days=seed_start.weekday())

    for index, config in enumerate(PARK_CONFIGS):
        accessibility_score = calculate_accessibility_score(
            airport_access_score=config.airport_access_score,
            drive_access_score=config.drive_access_score,
            road_access_score=config.road_access_score,
            seasonal_access_score=config.seasonal_access_score,
        )
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
            nearest_major_airport=config.nearest_major_airport,
            distance_to_nearest_airport_miles=config.distance_to_nearest_airport_miles,
            nearest_city=config.nearest_city,
            distance_from_nearest_city=config.distance_from_nearest_city,
            road_access_description=config.road_access_description,
            seasonal_access_description=config.seasonal_access_description,
            accessibility_score=accessibility_score,
        )
        session.add(park)
        session.flush()

        historical_weekly_visits: list[int] = []
        for month_offset in range(12):
            month_date = date(seed_start.year, seed_start.month, 1) - timedelta(
                days=30 * (11 - month_offset)
            )
            visits = int(config.baseline_visits * (0.7 + 0.05 * (month_offset % 6))) + (
                index * 1100
            )
            historical_weekly_visits.append(int(visits / 4.345))
            session.add(
                ParkVisitationHistory(
                    park_id=park.id,
                    observation_month=month_date,
                    visits=visits,
                    data_source="seeded_mock",
                    source_updated_at=None,
                    ingested_at=datetime.now(timezone.utc),
                )
            )

        for week in range(FORECAST_WEEKS):
            week_start = seed_start + timedelta(days=7 * week)
            week_end = week_start + timedelta(days=6)
            predicted_visits = int(config.baseline_visits * (0.72 + 0.015 * week)) + (index * 650)
            crowd_score = calculate_crowd_score(
                predicted_weekly_visits=predicted_visits,
                historical_weekly_visits=historical_weekly_visits,
            )

            mean_temp_f = 50 + (12 * (1 - abs(12 - week) / 12)) - (index * 1.1)
            precipitation_probability = 65 - (week * 1.8) + (index * 1.2)
            weather_score = calculate_weather_score(
                temperature_f=mean_temp_f,
                precipitation_probability=max(0.0, min(100.0, precipitation_probability)),
            )
            trip_score = calculate_trip_score(crowd_score, weather_score, accessibility_score)

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
