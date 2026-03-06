"""Response schemas for park API endpoints."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class ParkBase(BaseModel):
    id: int
    name: str
    slug: str
    state: str
    latitude: float
    longitude: float

    model_config = ConfigDict(from_attributes=True)


class ParkListItem(ParkBase):
    accessibility_score: float
    crowd_score: float | None = None
    trip_score: float | None = None


class ParksMapDataItem(BaseModel):
    park_id: int
    name: str
    slug: str
    latitude: float
    longitude: float
    crowd_score: float | None = None
    crowd_level: str | None = None


class ParkDetail(ParkBase):
    airport_access_score: float
    drive_access_score: float
    road_access_score: float
    seasonal_access_score: float
    accessibility_score: float


class ForecastWeek(BaseModel):
    week_start: date
    week_end: date
    predicted_visits: int
    crowd_score: float
    weather_score: float
    accessibility_score: float
    trip_score: float

    model_config = ConfigDict(from_attributes=True)


class BestWeeksResponse(BaseModel):
    top_weeks: list[ForecastWeek]
    hidden_gem_weeks: list[ForecastWeek]


class CalendarWeek(BaseModel):
    forecast_id: int
    week_start: date
    week_end: date
    crowd_level: str
    color_hex: str
    crowd_score: float


class AccessibilityResponse(BaseModel):
    airport_access_score: float
    drive_access_score: float
    road_access_score: float
    seasonal_access_score: float
    accessibility_score: float


class AlertResponse(BaseModel):
    id: int
    title: str
    severity: str
    message: str
    starts_on: date
    ends_on: date
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
