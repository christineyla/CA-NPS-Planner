from collections.abc import Generator

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.db import Base
from app.jobs.forecast_generation import ForecastGenerationJob
from app.services.forecasting import ForecastRunner, WeeklyDisaggregator
from app.services.seed_data import FORECAST_WEEKS, PARK_CONFIGS, seed_database


@pytest.fixture()
def seeded_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with session_factory() as session:
        seed_database(session)
        yield session


def test_weekly_disaggregation_preserves_monthly_totals() -> None:
    monthly = pd.DataFrame(
        {
            "month_start": pd.to_datetime(["2026-01-01", "2026-02-01"]),
            "park_id": [1, 1],
            "predicted_visits": [10000, 12000],
        }
    )
    holiday_weeks = {pd.Timestamp("2026-01-05")}
    seasonal_weights = {1: 1.1, 2: 0.9}

    disaggregated = WeeklyDisaggregator().disaggregate(
        monthly_forecast=monthly,
        horizon_weeks=8,
        seasonal_weights=seasonal_weights,
        holiday_weeks=holiday_weeks,
    )

    monthly_totals = (
        disaggregated.groupby("month_start")["predicted_visits"].sum().sort_index().to_dict()
    )
    assert monthly_totals[pd.Timestamp("2026-01-01")] == 10000
    assert monthly_totals[pd.Timestamp("2026-02-01")] == 12000


def test_forecast_runner_outputs_park_specific_26_week_forecast() -> None:
    months = pd.date_range(start="2018-01-01", periods=96, freq="MS")
    history = pd.DataFrame(
        {
            "month_start": months,
            "visits": [70000 + i * 120 + ((i % 12) * 450) for i in range(len(months))],
        }
    )

    output = ForecastRunner().run_for_park(park_id=99, monthly_history=history, horizon_weeks=26, seed=7)

    assert len(output) == 26
    assert output["park_id"].nunique() == 1
    assert output["park_id"].iloc[0] == 99
    assert (output["predicted_visits"] >= 0).all()


def test_forecast_generation_job_writes_26_weeks_for_each_park(seeded_session: Session) -> None:
    seeded_session.query(models.ParkVisitationForecast).delete()
    seeded_session.commit()

    rows_written = ForecastGenerationJob().run(seeded_session)

    expected = len(PARK_CONFIGS) * FORECAST_WEEKS
    assert rows_written == expected

    rows_in_db = seeded_session.query(models.ParkVisitationForecast).count()
    assert rows_in_db == expected
