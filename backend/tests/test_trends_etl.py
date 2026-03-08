from datetime import date, datetime, timezone

import pandas as pd
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.jobs.etl_pipeline import GoogleTrendsHistoryETL
from app.models import ParkTrendHistory
from app.services import seed_database


class FakeTrendProvider:
    source_label = "Fake Google Trends Provider"

    def fetch_weekly_interest(
        self,
        query_by_slug: dict[str, str],
        start_date: date,
        end_date: date,
    ) -> tuple[pd.DataFrame, datetime | None]:
        rows: list[dict[str, object]] = []
        for i, slug in enumerate(query_by_slug.keys()):
            for week in pd.date_range(start="2021-01-04", end="2024-12-30", freq="W-MON"):
                rows.append(
                    {
                        "park_slug": slug,
                        "observation_date": week.date(),
                        "google_trends_index": float(40 + i),
                    }
                )
        # out-of-scope row should be filtered
        rows.append(
            {
                "park_slug": "pinnacles",
                "observation_date": date(2024, 7, 1),
                "google_trends_index": 99.0,
            }
        )
        return pd.DataFrame(rows), datetime(2025, 1, 1, tzinfo=timezone.utc)


class FailingTrendProvider:
    source_label = "Unavailable Trends Provider"

    def fetch_weekly_interest(
        self,
        query_by_slug: dict[str, str],
        start_date: date,
        end_date: date,
    ) -> tuple[pd.DataFrame, datetime | None]:
        raise RuntimeError("provider unavailable")


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


def test_trends_etl_filters_scope_and_applies_three_year_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _make_seeded_engine()
    etl = GoogleTrendsHistoryETL(provider=FakeTrendProvider(), lookback_years=3)
    monkeypatch.setattr(
        etl, "_window_dates", lambda reference_date: (date(2022, 1, 1), date(2024, 12, 31))
    )

    with Session(engine) as session:
        loaded = etl.run(session=session)

    with Session(engine) as session:
        rows = session.scalars(select(ParkTrendHistory)).all()

    assert loaded == len(rows)
    assert {row.park_id for row in rows}
    assert len({row.park_id for row in rows}) == 5
    assert min(row.observation_date for row in rows) >= date(2022, 1, 1)
    assert max(row.observation_date for row in rows) <= date(2024, 12, 31)


def test_trends_etl_populates_metadata_and_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = _make_seeded_engine()
    etl = GoogleTrendsHistoryETL(provider=FakeTrendProvider(), lookback_years=3)
    monkeypatch.setattr(
        etl, "_window_dates", lambda reference_date: (date(2022, 1, 1), date(2024, 12, 31))
    )

    with Session(engine) as session:
        first = etl.run(session=session)

    with Session(engine) as session:
        second = etl.run(session=session)

    with Session(engine) as session:
        rows = session.scalars(select(ParkTrendHistory)).all()
        unique_rows = session.scalar(
            select(func.count()).select_from(
                select(ParkTrendHistory.park_id, ParkTrendHistory.observation_date)
                .distinct()
                .subquery()
            )
        )

    assert first == second
    assert len(rows) == first
    assert unique_rows == first
    assert all(row.data_source == etl.provider.source_label for row in rows)
    assert all(row.source_updated_at is not None for row in rows)
    assert all(row.ingested_at is not None for row in rows)


def test_trends_etl_raises_when_provider_unavailable() -> None:
    engine = _make_seeded_engine()
    etl = GoogleTrendsHistoryETL(provider=FailingTrendProvider())

    with Session(engine) as session:
        with pytest.raises(RuntimeError, match="provider unavailable"):
            etl.run(session=session)
