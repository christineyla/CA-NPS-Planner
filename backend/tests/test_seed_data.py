from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models import CrowdCalendar, Park, ParkAlert, ParkVisitationForecast, ParkVisitationHistory
from app.services import FORECAST_WEEKS, PARK_CONFIGS, seed_database


def test_seed_database_creates_required_mock_data() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        seed_database(session)

    with Session(engine) as session:
        parks = session.scalars(select(Park)).all()
        forecasts = session.scalars(select(ParkVisitationForecast)).all()
        history = session.scalars(select(ParkVisitationHistory)).all()
        calendar = session.scalars(select(CrowdCalendar)).all()
        alerts = session.scalars(select(ParkAlert)).all()

    assert len(parks) == len(PARK_CONFIGS)
    assert len(forecasts) == len(PARK_CONFIGS) * FORECAST_WEEKS
    assert len(history) == len(PARK_CONFIGS) * 12
    assert len(calendar) == len(forecasts)
    assert len(alerts) >= len(PARK_CONFIGS)


def test_seed_database_alerts_cover_prd_disruptions() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        seed_database(session)

    with Session(engine) as session:
        alerts = session.scalars(select(ParkAlert)).all()

    assert len(alerts) == len(PARK_CONFIGS) * 3

    severities = {alert.severity.lower() for alert in alerts}
    assert {"yellow", "orange", "red"}.issubset(severities)

    alert_text = " ".join(f"{alert.title} {alert.message}".lower() for alert in alerts)
    for keyword in ["wildfire", "major road", "flood", "heat", "closure"]:
        assert keyword in alert_text

    assert any(alert.is_active and alert.severity.lower() == "red" for alert in alerts)
