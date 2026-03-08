from collections.abc import Generator
from datetime import date, datetime, timezone

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

    output = ForecastRunner().run_for_park(
        park_id=99, monthly_history=history, horizon_weeks=26, seed=7
    )

    assert len(output) == 26
    assert output["park_id"].nunique() == 1
    assert output["park_id"].iloc[0] == 99
    assert (output["predicted_visits"] >= 0).all()




def test_derive_forecast_start_date_uses_later_of_run_week_or_post_cutoff_week() -> None:
    job = ForecastGenerationJob()

    start_from_run_week = job._derive_forecast_start_date(
        data_cutoff_date=date(2026, 1, 15),
        run_context_date=date(2026, 2, 18),
    )
    assert start_from_run_week == date(2026, 2, 16)

    start_from_cutoff = job._derive_forecast_start_date(
        data_cutoff_date=date(2026, 3, 20),
        run_context_date=date(2026, 2, 18),
    )
    assert start_from_cutoff == date(2026, 3, 23)


def test_forecast_generation_starts_from_run_context_week(seeded_session: Session) -> None:
    seeded_session.query(models.ParkVisitationForecast).delete()
    seeded_session.query(models.CrowdCalendar).delete()
    seeded_session.commit()

    run_generated_at = datetime(2026, 4, 15, tzinfo=timezone.utc)
    rows_written = ForecastGenerationJob().run(seeded_session, generated_at=run_generated_at)
    assert rows_written == len(PARK_CONFIGS) * FORECAST_WEEKS

    first = (
        seeded_session.query(models.ParkVisitationForecast)
        .order_by(
            models.ParkVisitationForecast.park_id.asc(),
            models.ParkVisitationForecast.week_start.asc(),
        )
        .first()
    )
    assert first is not None
    assert first.week_start == date(2026, 4, 13)
    assert first.forecast_generated_at.date() == run_generated_at.date()

def test_forecast_generation_job_writes_26_weeks_for_each_park(seeded_session: Session) -> None:
    seeded_session.query(models.ParkVisitationForecast).delete()
    seeded_session.query(models.CrowdCalendar).delete()
    seeded_session.commit()

    rows_written = ForecastGenerationJob().run(seeded_session)

    expected = len(PARK_CONFIGS) * FORECAST_WEEKS
    assert rows_written == expected

    rows_in_db = seeded_session.query(models.ParkVisitationForecast).count()
    assert rows_in_db == expected


def test_forecast_generation_updates_metadata_fields(seeded_session: Session) -> None:
    seeded_session.query(models.ParkVisitationForecast).delete()
    seeded_session.query(models.CrowdCalendar).delete()
    seeded_session.commit()

    rows_written = ForecastGenerationJob().run(seeded_session)
    assert rows_written == len(PARK_CONFIGS) * FORECAST_WEEKS

    first = (
        seeded_session.query(models.ParkVisitationForecast)
        .order_by(
            models.ParkVisitationForecast.park_id.asc(),
            models.ParkVisitationForecast.week_start.asc(),
        )
        .first()
    )
    assert first is not None
    assert first.forecast_generated_at is not None
    assert first.model_trained_at is not None
    assert first.data_cutoff_date is not None
    assert first.model_version == "forecast-pipeline-v1"


def test_forecast_generation_uses_trend_history_when_available(seeded_session: Session) -> None:
    park = seeded_session.query(models.Park).order_by(models.Park.id.asc()).first()
    assert park is not None

    seeded_session.add_all(
        [
            models.ParkTrendHistory(
                park_id=park.id,
                observation_date=date(2025, 1, 6),
                google_trends_index=95.0,
                data_source="test-trends",
                source_updated_at=None,
                ingested_at=pd.Timestamp("2025-02-01").to_pydatetime(),
            ),
            models.ParkTrendHistory(
                park_id=park.id,
                observation_date=date(2025, 1, 13),
                google_trends_index=90.0,
                data_source="test-trends",
                source_updated_at=None,
                ingested_at=pd.Timestamp("2025-02-01").to_pydatetime(),
            ),
        ]
    )
    seeded_session.commit()

    rows_written = ForecastGenerationJob().run(seeded_session)
    assert rows_written == len(PARK_CONFIGS) * FORECAST_WEEKS


def test_forecast_generation_uses_weather_history_when_available(seeded_session: Session) -> None:
    rows_written = ForecastGenerationJob().run(seeded_session)
    assert rows_written == len(PARK_CONFIGS) * FORECAST_WEEKS

    scores = seeded_session.query(models.ParkVisitationForecast.weather_score).all()
    assert len(scores) == len(PARK_CONFIGS) * FORECAST_WEEKS


def test_forecast_generation_fallbacks_when_optional_inputs_absent(seeded_session: Session) -> None:
    seeded_session.query(models.ParkTrendHistory).delete()
    seeded_session.query(models.ParkWeatherHistory).delete()
    seeded_session.query(models.ParkVisitationForecast).delete()
    seeded_session.query(models.CrowdCalendar).delete()
    seeded_session.commit()

    rows_written = ForecastGenerationJob().run(seeded_session)
    assert rows_written == len(PARK_CONFIGS) * FORECAST_WEEKS

    calendar_count = seeded_session.query(models.CrowdCalendar).count()
    assert calendar_count == len(PARK_CONFIGS) * FORECAST_WEEKS
