from datetime import date

import pandas as pd
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.db import Base
from app.jobs.etl_pipeline import IN_SCOPE_PARK_WEATHER_POINTS, MeteostatWeatherETL
from app.jobs.forecast_generation import ForecastGenerationJob
from app.models import ParkVisitationForecast, ParkWeatherHistory
from app.services import seed_database


def _make_seeded_engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        seed_database(session)

    return engine


def _fake_weather_frame(start: date, end: date, temp_offset: float = 0.0) -> pd.DataFrame:
    dates = pd.date_range(start=start, end=end, freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "tavg": [15.0 + temp_offset] * len(dates),
            "tmin": [7.0 + temp_offset] * len(dates),
            "tmax": [22.0 + temp_offset] * len(dates),
            "prcp": [1.5] * len(dates),
        }
    )


def test_weather_etl_loads_only_in_scope_parks_and_enforces_three_year_window(
    monkeypatch,
) -> None:
    engine = _make_seeded_engine()
    etl = MeteostatWeatherETL(lookback_years=3)
    start_date, end_date = date(2023, 1, 1), date(2025, 7, 31)
    monkeypatch.setattr(etl, "_window_dates", lambda reference_date: (start_date, end_date))

    in_scope_frames = {
        slug: _fake_weather_frame(start=start_date, end=end_date)
        for slug in IN_SCOPE_PARK_WEATHER_POINTS
    }
    # include extra out-of-scope key; ETL should ignore it
    in_scope_frames["pinnacles"] = _fake_weather_frame(start=start_date, end=end_date)

    with Session(engine) as session:
        loaded = etl.run(session=session, weather_data_by_slug=in_scope_frames)

    with Session(engine) as session:
        rows = session.scalars(select(ParkWeatherHistory)).all()

    assert loaded == len(rows)
    assert {row.park_id for row in rows} == {1, 2, 3, 4, 5}
    assert min(row.observation_date for row in rows) == start_date
    assert max(row.observation_date for row in rows) == end_date


def test_weather_etl_populates_metadata_and_is_idempotent(monkeypatch) -> None:
    engine = _make_seeded_engine()
    etl = MeteostatWeatherETL(lookback_years=3)
    start_date, end_date = date(2023, 1, 1), date(2025, 7, 31)
    monkeypatch.setattr(etl, "_window_dates", lambda reference_date: (start_date, end_date))

    weather_data = {
        slug: _fake_weather_frame(start=start_date, end=end_date, temp_offset=float(i))
        for i, slug in enumerate(IN_SCOPE_PARK_WEATHER_POINTS.keys())
    }

    with Session(engine) as session:
        first = etl.run(session=session, weather_data_by_slug=weather_data)

    with Session(engine) as session:
        second = etl.run(session=session, weather_data_by_slug=weather_data)

    with Session(engine) as session:
        rows = session.scalars(select(ParkWeatherHistory)).all()
        unique_rows = session.scalar(
            select(func.count()).select_from(
                select(ParkWeatherHistory.park_id, ParkWeatherHistory.observation_date)
                .distinct()
                .subquery()
            )
        )

    assert first == second
    assert len(rows) == first
    assert unique_rows == first
    assert all(row.data_source == etl.source_label for row in rows)
    assert all(row.source_updated_at is None for row in rows)
    assert all(row.ingested_at is not None for row in rows)


def test_weather_etl_output_is_used_by_forecast_weather_score_logic(monkeypatch) -> None:
    engine = _make_seeded_engine()
    etl = MeteostatWeatherETL(lookback_years=3)
    start_date, end_date = date(2023, 1, 1), date(2025, 7, 31)
    monkeypatch.setattr(etl, "_window_dates", lambda reference_date: (start_date, end_date))

    # low-comfort monthly temps/precip to ensure output differs from seeded fallback weather score
    weather_data = {
        slug: pd.DataFrame(
            {
                "date": pd.date_range(start=start_date, end=end_date, freq="D"),
                "tavg": [35.0] * ((end_date - start_date).days + 1),
                "tmin": [30.0] * ((end_date - start_date).days + 1),
                "tmax": [40.0] * ((end_date - start_date).days + 1),
                "prcp": [9.0] * ((end_date - start_date).days + 1),
            }
        )
        for slug in IN_SCOPE_PARK_WEATHER_POINTS
    }

    with Session(engine) as session:
        etl.run(session=session, weather_data_by_slug=weather_data)

    job = ForecastGenerationJob()

    with Session(engine) as session:
        session.query(ParkVisitationForecast).delete()
        session.commit()
        written = job.run(session)

    with Session(engine) as session:
        first_park_id = 1
        monthly_weather = job._load_monthly_weather_by_month_start(
            session=session, park_id=first_park_id
        )

    assert written > 0
    assert monthly_weather

    weather_score_from_real_weather = job._weather_score_for_week(
        weather_by_month=monthly_weather,
        month_start=pd.Timestamp("2024-07-01"),
    )
    fallback_score = job._weather_score_for_week(
        weather_by_month=monthly_weather,
        month_start=pd.Timestamp("2035-01-01"),
    )

    assert weather_score_from_real_weather <= 50
    assert fallback_score == 92
