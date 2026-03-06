"""Feature engineering helpers for forecasting and adjustment layers."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class FeatureEngineer:
    """Build lagged, rolling, holiday, and trend signals for forecast adjustment."""

    def build_weekly_features(
        self,
        weekly_frame: pd.DataFrame,
        holiday_weeks: set[pd.Timestamp] | None = None,
    ) -> pd.DataFrame:
        """Return a feature table suitable for model adjustment."""

        holiday_weeks = holiday_weeks or set()

        frame = weekly_frame.sort_values("week_start").reset_index(drop=True).copy()
        frame["lag_1"] = frame["predicted_visits"].shift(1).bfill()
        frame["lag_2"] = frame["predicted_visits"].shift(2).bfill()
        frame["rolling_4w_avg"] = frame["predicted_visits"].rolling(window=4, min_periods=1).mean()
        frame["holiday_proximity"] = frame["week_start"].map(
            lambda dt: 1 if dt in holiday_weeks else 0
        )
        frame["trend_signal"] = frame.index.astype(float) / max(len(frame) - 1, 1)

        if "weather_anomaly" not in frame:
            frame["weather_anomaly"] = 0.0
        if "google_trends_index" not in frame:
            frame["google_trends_index"] = 50.0
        if "sme_index" not in frame:
            frame["sme_index"] = 50.0

        return frame
