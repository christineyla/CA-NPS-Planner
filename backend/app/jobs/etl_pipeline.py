"""Data ingestion and normalization job for forecast model inputs."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


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
