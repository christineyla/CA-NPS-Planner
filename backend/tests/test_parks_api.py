from collections.abc import Generator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.db import Base, get_session
from app.main import app
from app.services import FORECAST_WEEKS, PARK_CONFIGS, seed_database


@pytest.fixture()
def seeded_client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)

    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with Session(engine) as session:
        seed_database(session)

    def _override_session() -> Generator[Session, None, None]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_parks_endpoints_return_seeded_data(seeded_client: TestClient) -> None:
    parks_response = seeded_client.get("/parks")
    assert parks_response.status_code == 200
    parks_payload = parks_response.json()
    assert len(parks_payload) == len(PARK_CONFIGS)

    first_park_id = parks_payload[0]["id"]

    map_response = seeded_client.get("/parks/map-data")
    assert map_response.status_code == 200
    assert len(map_response.json()) == len(PARK_CONFIGS)

    detail_response = seeded_client.get(f"/parks/{first_park_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == first_park_id

    forecast_response = seeded_client.get(f"/parks/{first_park_id}/forecast")
    assert forecast_response.status_code == 200
    assert len(forecast_response.json()) == FORECAST_WEEKS

    best_weeks_response = seeded_client.get(f"/parks/{first_park_id}/best-weeks")
    assert best_weeks_response.status_code == 200
    best_weeks_payload = best_weeks_response.json()
    assert len(best_weeks_payload["top_weeks"]) == 5
    assert "hidden_gem_weeks" in best_weeks_payload

    calendar_response = seeded_client.get(f"/parks/{first_park_id}/calendar")
    assert calendar_response.status_code == 200
    assert len(calendar_response.json()) == FORECAST_WEEKS

    accessibility_response = seeded_client.get(f"/parks/{first_park_id}/accessibility")
    assert accessibility_response.status_code == 200
    accessibility_payload = accessibility_response.json()
    assert "accessibility_score" in accessibility_payload
    assert "nearest_major_airport" in accessibility_payload
    assert "distance_to_nearest_airport_miles" in accessibility_payload
    assert "nearest_city" in accessibility_payload
    assert "distance_from_nearest_city" in accessibility_payload
    assert "road_access_description" in accessibility_payload
    assert "seasonal_access_description" in accessibility_payload

    alerts_response = seeded_client.get(f"/parks/{first_park_id}/alerts")
    assert alerts_response.status_code == 200
    assert len(alerts_response.json()) >= 1


def test_park_not_found_returns_404(seeded_client: TestClient) -> None:
    response = seeded_client.get("/parks/99999")

    assert response.status_code == 404


def test_best_weeks_exclude_red_alert_windows(seeded_client: TestClient) -> None:
    parks_payload = seeded_client.get("/parks").json()
    first_park_id = parks_payload[0]["id"]

    best_weeks_payload = seeded_client.get(f"/parks/{first_park_id}/best-weeks").json()
    alerts_payload = seeded_client.get(f"/parks/{first_park_id}/alerts").json()
    red_alerts = [
        alert for alert in alerts_payload if alert["is_active"] and alert["severity"].lower() == "red"
    ]
    assert red_alerts

    for week in best_weeks_payload["top_weeks"]:
        week_start = date.fromisoformat(week["week_start"])
        week_end = date.fromisoformat(week["week_end"])
        assert not any(
            week_start <= date.fromisoformat(alert["ends_on"])
            and week_end >= date.fromisoformat(alert["starts_on"])
            for alert in red_alerts
        )
