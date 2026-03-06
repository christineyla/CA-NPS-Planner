"""Park data endpoints backed by seeded mock records."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas.parks import (
    AccessibilityResponse,
    AlertResponse,
    BestWeeksResponse,
    CalendarWeek,
    ForecastWeek,
    ParkDetail,
    ParkListItem,
    ParksMapDataItem,
)
from app.services.park_queries import (
    get_alerts,
    get_best_weeks,
    get_crowd_calendar,
    get_hidden_gem_weeks,
    get_latest_forecast_for_parks,
    get_park_forecast,
    get_park_or_none,
    get_parks,
)

router = APIRouter(prefix="/parks", tags=["parks"])


def _require_park(session: Session, park_id: int):
    park = get_park_or_none(session, park_id)
    if park is None:
        raise HTTPException(status_code=404, detail=f"Park {park_id} not found")
    return park


@router.get("", response_model=list[ParkListItem])
def list_parks(session: Session = Depends(get_session)) -> list[ParkListItem]:
    parks = get_parks(session)
    latest_forecast = get_latest_forecast_for_parks(session)

    return [
        ParkListItem(
            id=park.id,
            name=park.name,
            slug=park.slug,
            state=park.state,
            latitude=park.latitude,
            longitude=park.longitude,
            accessibility_score=park.accessibility_score,
            crowd_score=latest_forecast.get(park.id).crowd_score if latest_forecast.get(park.id) else None,
            trip_score=latest_forecast.get(park.id).trip_score if latest_forecast.get(park.id) else None,
        )
        for park in parks
    ]


@router.get("/map-data", response_model=list[ParksMapDataItem])
def parks_map_data(session: Session = Depends(get_session)) -> list[ParksMapDataItem]:
    parks = get_parks(session)
    latest_forecast = get_latest_forecast_for_parks(session)

    map_data: list[ParksMapDataItem] = []
    for park in parks:
        forecast = latest_forecast.get(park.id)
        crowd_level: str | None = None
        if forecast is not None:
            if forecast.crowd_score <= 30:
                crowd_level = "low"
            elif forecast.crowd_score <= 60:
                crowd_level = "moderate"
            elif forecast.crowd_score <= 80:
                crowd_level = "busy"
            else:
                crowd_level = "extreme"

        map_data.append(
            ParksMapDataItem(
                park_id=park.id,
                name=park.name,
                slug=park.slug,
                latitude=park.latitude,
                longitude=park.longitude,
                crowd_score=forecast.crowd_score if forecast else None,
                crowd_level=crowd_level,
            )
        )

    return map_data


@router.get("/{park_id}", response_model=ParkDetail)
def get_park(park_id: int, session: Session = Depends(get_session)) -> ParkDetail:
    return _require_park(session, park_id)


@router.get("/{park_id}/forecast", response_model=list[ForecastWeek])
def park_forecast(park_id: int, session: Session = Depends(get_session)) -> list[ForecastWeek]:
    _require_park(session, park_id)
    return list(get_park_forecast(session, park_id))


@router.get("/{park_id}/best-weeks", response_model=BestWeeksResponse)
def park_best_weeks(park_id: int, session: Session = Depends(get_session)) -> BestWeeksResponse:
    _require_park(session, park_id)
    return BestWeeksResponse(
        top_weeks=list(get_best_weeks(session, park_id, limit=5)),
        hidden_gem_weeks=list(get_hidden_gem_weeks(session, park_id)),
    )


@router.get("/{park_id}/calendar", response_model=list[CalendarWeek])
def park_calendar(park_id: int, session: Session = Depends(get_session)) -> list[CalendarWeek]:
    _require_park(session, park_id)
    entries = get_crowd_calendar(session, park_id)
    return [
        CalendarWeek(
            forecast_id=entry.forecast_id,
            week_start=entry.forecast.week_start,
            week_end=entry.forecast.week_end,
            crowd_level=entry.crowd_level,
            color_hex=entry.color_hex,
            crowd_score=entry.crowd_score,
        )
        for entry in entries
    ]


@router.get("/{park_id}/accessibility", response_model=AccessibilityResponse)
def park_accessibility(park_id: int, session: Session = Depends(get_session)) -> AccessibilityResponse:
    park = _require_park(session, park_id)
    return AccessibilityResponse(
        airport_access_score=park.airport_access_score,
        drive_access_score=park.drive_access_score,
        road_access_score=park.road_access_score,
        seasonal_access_score=park.seasonal_access_score,
        accessibility_score=park.accessibility_score,
    )


@router.get("/{park_id}/alerts", response_model=list[AlertResponse])
def park_alerts(park_id: int, session: Session = Depends(get_session)) -> list[AlertResponse]:
    _require_park(session, park_id)
    return list(get_alerts(session, park_id))
