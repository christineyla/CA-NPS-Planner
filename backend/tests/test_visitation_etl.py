import csv
import json
from datetime import date, datetime, timezone
from io import StringIO

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.jobs import NPSVisitationETL
from app.models import Park, ParkVisitationHistory
from app.services import seed_database


def _build_source_csv() -> bytes:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=["ParkName", "Month", "RecreationVisits"])
    writer.writeheader()

    in_scope = [
        "Yosemite National Park",
        "Joshua Tree National Park",
        "Death Valley National Park",
        "Sequoia National Park",
        "Kings Canyon National Park",
    ]

    for park_name in in_scope:
        for year in [2021, 2022, 2023, 2024]:
            for month in [1, 7]:
                writer.writerow(
                    {
                        "ParkName": park_name,
                        "Month": f"{year}-{month:02d}-01",
                        "RecreationVisits": (year - 2020) * 1000 + month,
                    }
                )

    # out-of-scope should be ignored
    writer.writerow(
        {
            "ParkName": "Pinnacles National Park",
            "Month": "2024-07-01",
            "RecreationVisits": 5555,
        }
    )

    return output.getvalue().encode("utf-8")


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


def test_visitation_etl_filters_scope_and_enforces_three_year_window() -> None:
    engine = _make_seeded_engine()
    etl = NPSVisitationETL(lookback_years=3)

    with Session(engine) as session:
        loaded = etl.run(
            session=session,
            csv_payload=_build_source_csv(),
            source_updated_at=datetime(2025, 1, 15, tzinfo=timezone.utc),  # noqa: UP017
        )

    with Session(engine) as session:
        history = session.scalars(select(ParkVisitationHistory)).all()

    assert loaded == 5 * 6  # 2022-2024 x 2 months x 5 parks
    assert len(history) == loaded

    park_ids = {row.park_id for row in history}
    assert len(park_ids) == 5
    assert min(row.observation_month for row in history) == date(2022, 1, 1)
    assert max(row.observation_month for row in history) == date(2024, 7, 1)


def test_visitation_etl_populates_metadata_and_is_duplicate_safe() -> None:
    engine = _make_seeded_engine()
    etl = NPSVisitationETL(lookback_years=3)
    source_updated_at = datetime(2025, 2, 1, tzinfo=timezone.utc)  # noqa: UP017

    with Session(engine) as session:
        first_count = etl.run(
            session=session,
            csv_payload=_build_source_csv(),
            source_updated_at=source_updated_at,
        )

    with Session(engine) as session:
        second_count = etl.run(
            session=session,
            csv_payload=_build_source_csv(),
            source_updated_at=source_updated_at,
        )

    with Session(engine) as session:
        history = session.scalars(select(ParkVisitationHistory)).all()
        unique_rows = session.scalar(
            select(func.count()).select_from(
                select(ParkVisitationHistory.park_id, ParkVisitationHistory.observation_month)
                .distinct()
                .subquery()
            )
        )

    assert first_count == second_count
    assert len(history) == first_count
    assert unique_rows == first_count

    assert all(row.data_source == etl.source_label for row in history)
    expected_source_updated = source_updated_at.replace(tzinfo=None)
    assert all(row.source_updated_at == expected_source_updated for row in history)
    assert all(row.ingested_at is not None for row in history)


def test_visitation_etl_raises_when_in_scope_park_metadata_missing() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        session.add(
            Park(
                name="Yosemite National Park",
                slug="yosemite",
                state="CA",
                latitude=37.8651,
                longitude=-119.5383,
                airport_access_score=1,
                drive_access_score=1,
                road_access_score=1,
                seasonal_access_score=1,
                accessibility_score=1,
                nearest_major_airport="FAT",
                distance_to_nearest_airport_miles=90,
                nearest_city="Fresno",
                distance_from_nearest_city="65 miles",
                road_access_description="x",
                seasonal_access_description="y",
            )
        )
        session.commit()

    with Session(engine) as session:
        try:
            NPSVisitationETL().run(session=session, csv_payload=_build_source_csv())
            assert False, "Expected missing park metadata error"
        except ValueError as exc:
            assert "in-scope parks" in str(exc)


def test_visitation_etl_resolves_correct_datagov_package_and_falls_back_when_irma_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _make_seeded_engine()
    etl = NPSVisitationETL(lookback_years=3)

    calls: list[str] = []

    def fake_download(url: str) -> bytes:
        calls.append(url)
        if url == etl.source_url:
            raise RuntimeError("HTTP request failed for IRMA: 500 Server Error")
        if "package_show?id=nps-visitor-use-statistics-data-package-2024" in url:
            # Existing slug can drift and resolve to a different package title.
            return json.dumps(
                {
                    "success": True,
                    "result": {
                        "title": "NPS Visitor Use Statistics Data Package, 2023",
                        "resources": [],
                    },
                }
            ).encode("utf-8")
        if "package_show?id=nps-visitor-use-statistics" in url:
            raise RuntimeError("404 Not Found")
        if "package_show?id=national-park-service-visitor-use-statistics" in url:
            raise RuntimeError("404 Not Found")
        if "package_search" in url:
            return json.dumps(
                {
                    "success": True,
                    "result": {
                        "results": [
                            {
                                "name": "official-2024-package",
                                "title": "NPS Visitor Use Statistics Data Package, 2024",
                            }
                        ]
                    },
                }
            ).encode("utf-8")
        if "package_show?id=official-2024-package" in url:
            package = {
                "success": True,
                "result": {
                    "title": "NPS Visitor Use Statistics Data Package, 2024",
                    "metadata_modified": "2025-03-01T00:00:00.000000",
                    "resources": [
                        {
                            "name": "Main_Data.csv",
                            "format": "CSV",
                            "url": "https://example.test/Main_Data.csv",
                        },
                        {
                            "name": "Readme",
                            "format": "TXT",
                            "url": "https://example.test/readme.txt",
                        },
                    ],
                },
            }
            return json.dumps(package).encode("utf-8")
        if "example.test/Main_Data.csv" in url:
            return _build_source_csv()
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(etl, "_download_source_payload", fake_download)

    with Session(engine) as session:
        loaded = etl.run(session=session)

    with Session(engine) as session:
        history = session.scalars(select(ParkVisitationHistory)).all()

    assert loaded == 5 * 6
    assert len(history) == loaded
    assert any("package_search" in url for url in calls)
    assert any("package_show?id=official-2024-package" in url for url in calls)
    assert any("example.test/Main_Data.csv" in url for url in calls)
    assert all(row.data_source == etl.fallback_source_label for row in history)


def test_visitation_etl_raises_clear_error_when_irma_and_datagov_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _make_seeded_engine()
    etl = NPSVisitationETL()

    def always_fail(url: str) -> bytes:
        if url == etl.source_url:
            raise RuntimeError("HTTP request failed for IRMA: 500 Server Error")
        raise RuntimeError("HTTP request failed for Data.gov: 503 Service Unavailable")

    monkeypatch.setattr(etl, "_download_source_payload", always_fail)

    with Session(engine) as session:
        with pytest.raises(RuntimeError, match="both official IRMA and Data.gov sources"):
            etl.run(session=session)


def test_visitation_etl_fallback_errors_when_datagov_resource_cannot_be_resolved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _make_seeded_engine()
    etl = NPSVisitationETL()

    def fake_download(url: str) -> bytes:
        if url == etl.source_url:
            raise RuntimeError("HTTP request failed for IRMA: 500 Server Error")
        if "package_show" in url:
            return json.dumps(
                {
                    "success": True,
                    "result": {
                        "title": "NPS Visitor Use Statistics Data Package, 2024",
                        "resources": [
                            {
                                "name": "Documentation",
                                "format": "HTML",
                                "url": "https://example.test/docs",
                            }
                        ],
                    },
                }
            ).encode("utf-8")
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(etl, "_download_source_payload", fake_download)

    with Session(engine) as session:
        with pytest.raises(RuntimeError, match="main visitation CSV resource"):
            etl.run(session=session)
