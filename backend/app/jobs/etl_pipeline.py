"""Data ingestion and normalization job for forecast model inputs."""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from io import BytesIO
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Park, ParkVisitationHistory

NPS_MONTHLY_SOURCE = "NPS Visitor Use Statistics (IRMA monthly visitation package)"
NPS_MONTHLY_FALLBACK_SOURCE = "NPS Visitor Use Statistics (Data.gov data package resource)"
NPS_MONTHLY_ZIP_URL = (
    "https://irma.nps.gov/STATS/FileDownloadHandler.ashx?type=V&filename=Reports%2F"
    "AnnualVisitationByPark%281979%20-%20Last%20Calendar%20Year%29.zip"
)
DATA_GOV_PACKAGE_API_URL = "https://catalog.data.gov/api/3/action/package_show"
DATA_GOV_PACKAGE_IDS = (
    "nps-visitor-use-statistics",
    "national-park-service-visitor-use-statistics",
)
DATA_GOV_PRIMARY_RESOURCE_KEYWORDS = (
    "annual park recreation visitation",
    "1904",
    "last calendar year",
)
IN_SCOPE_PARK_NAMES = {
    "Yosemite National Park": "yosemite",
    "Joshua Tree National Park": "joshua-tree",
    "Death Valley National Park": "death-valley",
    "Sequoia National Park": "sequoia",
    "Kings Canyon National Park": "kings-canyon",
}


@dataclass
class ETLPipeline:
    """Ingest visitation/weather data and normalize to model-ready monthly history."""

    seed: int = 42

    def run(
        self,
        park_id: int,
        months: int = 120,
        visitation_data: pd.DataFrame | None = None,
        weather_data: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """Return a normalized monthly dataset for model training and forecast generation."""

        if visitation_data is None:
            visitation_data = self._mock_visitation(park_id=park_id, months=months)
        if weather_data is None:
            weather_data = self._mock_weather(months=months)

        frame = visitation_data.merge(weather_data, on="month_start", how="left")
        frame["park_id"] = park_id
        frame["visits"] = frame["visits"].round().clip(lower=0).astype(int)
        frame["weather_anomaly"] = frame["weather_anomaly"].fillna(0.0)
        return frame[["park_id", "month_start", "visits", "weather_anomaly"]]

    def _mock_visitation(self, park_id: int, months: int) -> pd.DataFrame:
        rng = np.random.default_rng(self.seed + park_id)
        month_start = pd.date_range(start="2015-01-01", periods=months, freq="MS")
        seasonal = np.sin(np.arange(months) * 2 * np.pi / 12) * 18000
        trend = np.arange(months) * 110
        base = 90000 + (park_id * 1300)
        visits = base + seasonal + trend + rng.normal(0, 2500, size=months)
        return pd.DataFrame({"month_start": month_start, "visits": visits})

    def _mock_weather(self, months: int) -> pd.DataFrame:
        rng = np.random.default_rng(self.seed)
        month_start = pd.date_range(start="2015-01-01", periods=months, freq="MS")
        anomalies = rng.normal(0, 0.4, size=months)
        return pd.DataFrame({"month_start": month_start, "weather_anomaly": anomalies})


@dataclass
class NPSVisitationETL:
    """Extract, transform, and load NPS monthly visitation for in-scope California parks."""

    source_url: str = NPS_MONTHLY_ZIP_URL
    source_label: str = NPS_MONTHLY_SOURCE
    fallback_source_label: str = NPS_MONTHLY_FALLBACK_SOURCE
    lookback_years: int = 3

    def run(
        self,
        session: Session,
        csv_payload: bytes | None = None,
        source_updated_at: datetime | None = None,
    ) -> int:
        """Load normalized monthly visitation history into park_visitation_history."""

        parks_by_slug = self._fetch_in_scope_parks(session)
        if len(parks_by_slug) != len(IN_SCOPE_PARK_NAMES):
            raise ValueError(
                "Expected all in-scope parks to be present before running visitation ETL"
            )

        source_label = self.source_label
        payload = csv_payload
        if payload is None:
            payload, source_label, source_updated_at = self._download_with_fallback(
                source_updated_at
            )

        transformed = self._transform_csv_payload(payload=payload, parks_by_slug=parks_by_slug)
        if transformed.empty:
            return 0

        source_timestamp = source_updated_at or self._infer_source_updated_at(payload)
        ingested_at = datetime.now(timezone.utc)  # noqa: UP017
        transformed["data_source"] = source_label
        transformed["source_updated_at"] = source_timestamp
        transformed["ingested_at"] = ingested_at

        self._replace_window(session=session, transformed=transformed)
        return int(len(transformed))

    def _fetch_in_scope_parks(self, session: Session) -> dict[str, Park]:
        parks = session.scalars(
            select(Park).where(Park.slug.in_(IN_SCOPE_PARK_NAMES.values()))
        ).all()
        return {park.slug: park for park in parks}

    def _download_with_fallback(
        self, source_updated_at: datetime | None
    ) -> tuple[bytes, str, datetime | None]:
        """Download IRMA source first, then fallback to Data.gov official package on HTTP failure.

        We preserve the current official-source strategy by preferring IRMA's direct package URL.
        When IRMA returns an HTTP failure (including recent 500s), we fetch the official Data.gov
        package metadata and download the primary monthly visitation resource instead.
        """

        irma_errors: list[str] = []
        try:
            payload = self._download_source_payload(self.source_url)
            inferred_source_updated = source_updated_at or self._infer_source_updated_at(payload)
            return payload, self.source_label, inferred_source_updated
        except RuntimeError as exc:
            irma_errors.append(str(exc))

        try:
            payload, fallback_updated_at = self._download_datagov_fallback_payload()
            resolved_updated_at = (
                source_updated_at or fallback_updated_at or self._infer_source_updated_at(payload)
            )
            return payload, self.fallback_source_label, resolved_updated_at
        except RuntimeError as exc:
            irma_detail = "; ".join(irma_errors) if irma_errors else "unknown IRMA error"
            raise RuntimeError(
                "Failed to download NPS visitation data from both official IRMA and Data.gov "
                f"sources. IRMA error: {irma_detail}. Data.gov error: {exc}"
            ) from exc

    def _download_source_payload(self, url: str) -> bytes:
        try:
            import requests
        except ImportError as exc:  # pragma: no cover - validated in docs and runtime use
            raise RuntimeError(
                "The visitation ETL requires the requests package to download source data."
            ) from exc

        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            return response.content
        except requests.RequestException as exc:
            raise RuntimeError(f"HTTP request failed for {url}: {exc}") from exc

    def _download_datagov_fallback_payload(self) -> tuple[bytes, datetime | None]:
        package_metadata = self._download_datagov_package_metadata()
        resource_url = self._select_datagov_primary_resource_url(package_metadata)
        payload = self._download_source_payload(resource_url)
        return payload, self._parse_datagov_updated_at(package_metadata)

    def _download_datagov_package_metadata(self) -> dict[str, Any]:
        errors: list[str] = []
        for package_id in DATA_GOV_PACKAGE_IDS:
            api_url = f"{DATA_GOV_PACKAGE_API_URL}?id={package_id}"
            try:
                payload = self._download_source_payload(api_url)
                package = json.loads(payload.decode("utf-8"))
                if bool(package.get("success")) and isinstance(package.get("result"), dict):
                    return package["result"]
                errors.append(f"{package_id}: malformed package response")
            except Exception as exc:  # noqa: BLE001 - collect each candidate error
                errors.append(f"{package_id}: {exc}")

        raise RuntimeError("; ".join(errors) or "unable to resolve Data.gov package metadata")

    def _select_datagov_primary_resource_url(self, package_metadata: dict[str, Any]) -> str:
        resources = package_metadata.get("resources")
        if not isinstance(resources, list) or not resources:
            raise RuntimeError("Data.gov package did not include resources")

        def _resource_score(resource: dict[str, Any]) -> int:
            name = str(resource.get("name", "")).lower()
            description = str(resource.get("description", "")).lower()
            format_value = str(resource.get("format", "")).lower()

            score = 0
            haystack = f"{name} {description}"
            for keyword in DATA_GOV_PRIMARY_RESOURCE_KEYWORDS:
                if keyword in haystack:
                    score += 3
            if "visitation" in haystack:
                score += 2
            if "monthly" in haystack:
                score += 1
            if format_value == "csv":
                score += 2
            return score

        sorted_resources = sorted(resources, key=_resource_score, reverse=True)
        resource_url = sorted_resources[0].get("url")
        if not resource_url:
            raise RuntimeError(
                "Data.gov primary visitation resource did not include a downloadable URL"
            )
        return str(resource_url)

    def _parse_datagov_updated_at(self, package_metadata: dict[str, Any]) -> datetime | None:
        for field in ("metadata_modified", "metadata_created"):
            value = package_metadata.get(field)
            if not value:
                continue
            parsed = pd.to_datetime(value, utc=True, errors="coerce")
            if pd.isna(parsed):
                continue
            return parsed.to_pydatetime()
        return None

    def _transform_csv_payload(
        self, payload: bytes, parks_by_slug: dict[str, Park]
    ) -> pd.DataFrame:
        frame = self._read_monthly_visitation_frame(payload)

        frame = frame.rename(
            columns={"ParkName": "park_name", "Month": "month", "RecreationVisits": "visits"}
        )
        frame = frame[["park_name", "month", "visits"]].copy()
        frame["park_name"] = frame["park_name"].astype(str).str.strip()
        frame = frame[frame["park_name"].isin(IN_SCOPE_PARK_NAMES.keys())]

        frame["park_slug"] = frame["park_name"].map(IN_SCOPE_PARK_NAMES)
        frame["park_id"] = frame["park_slug"].map(
            {slug: park.id for slug, park in parks_by_slug.items()}
        )
        frame["observation_month"] = pd.to_datetime(frame["month"], errors="coerce").dt.date
        frame["visits"] = pd.to_numeric(frame["visits"], errors="coerce")
        frame = frame.dropna(subset=["park_id", "observation_month", "visits"])
        frame["park_id"] = frame["park_id"].astype(int)
        frame["visits"] = frame["visits"].round().astype(int)

        cutoff = self._window_start(reference_date=max(frame["observation_month"]))
        frame = frame[frame["observation_month"] >= cutoff]
        frame = frame.sort_values(["park_id", "observation_month"])
        return frame[["park_id", "observation_month", "visits"]].drop_duplicates(
            subset=["park_id", "observation_month"], keep="last"
        )

    def _read_monthly_visitation_frame(self, payload: bytes) -> pd.DataFrame:
        if payload[:2] == b"PK":
            with zipfile.ZipFile(BytesIO(payload)) as zf:
                csv_names = [name for name in zf.namelist() if name.lower().endswith(".csv")]
                if not csv_names:
                    raise ValueError("NPS visitation package did not include a CSV file")
                with zf.open(csv_names[0]) as csv_file:
                    return pd.read_csv(csv_file)

        return pd.read_csv(BytesIO(payload))

    def _infer_source_updated_at(self, payload: bytes) -> datetime | None:
        if payload[:2] != b"PK":
            return None

        with zipfile.ZipFile(BytesIO(payload)) as zf:
            entries = [info for info in zf.infolist() if not info.is_dir()]
            if not entries:
                return None
            newest = max(entries, key=lambda info: info.date_time)
            naive = datetime(*newest.date_time)
            return naive.replace(tzinfo=timezone.utc)  # noqa: UP017

    def _window_start(self, reference_date: date) -> date:
        return date(reference_date.year - self.lookback_years + 1, 1, 1)

    def _replace_window(self, session: Session, transformed: pd.DataFrame) -> None:
        keys = transformed[["park_id", "observation_month"]].drop_duplicates()
        min_month = transformed["observation_month"].min()

        park_ids = keys["park_id"].tolist()
        session.execute(
            delete(ParkVisitationHistory).where(
                ParkVisitationHistory.park_id.in_(park_ids),
                ParkVisitationHistory.observation_month >= min_month,
            )
        )

        session.add_all(
            [
                ParkVisitationHistory(
                    park_id=int(row.park_id),
                    observation_month=row.observation_month,
                    visits=int(row.visits),
                    data_source=str(row.data_source),
                    source_updated_at=row.source_updated_at,
                    ingested_at=row.ingested_at,
                )
                for row in transformed.itertuples(index=False)
            ]
        )
        session.commit()
