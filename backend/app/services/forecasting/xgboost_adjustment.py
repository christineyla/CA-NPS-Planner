"""XGBoost-style adjustment layer for weekly forecast corrections."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class XGBoostAdjustmentLayer:
    """Apply lightweight deterministic correction using engineered features."""

    seed: int = 42
    max_adjustment_ratio: float = 0.2

    def adjust(
        self,
        weekly_forecast: pd.DataFrame,
        feature_frame: pd.DataFrame,
    ) -> pd.DataFrame:
        """Apply park-level forecast adjustments with placeholder model logic."""

        merged = weekly_forecast.merge(
            feature_frame.drop(columns=["predicted_visits"]),
            on=["week_start", "week_end", "month_start"],
            how="left",
        )

        merged["adjustment_signal"] = (
            0.05 * ((merged["google_trends_index"] - 50.0) / 50.0)
            + 0.04 * ((merged["sme_index"] - 50.0) / 50.0)
            - 0.03 * merged["weather_anomaly"]
            + 0.02 * merged["holiday_proximity"]
            + 0.01 * ((merged["lag_1"] - merged["rolling_4w_avg"]) / merged["rolling_4w_avg"].clip(lower=1))
        )
        merged["adjustment_signal"] = merged["adjustment_signal"].clip(
            lower=-self.max_adjustment_ratio,
            upper=self.max_adjustment_ratio,
        )

        merged["predicted_visits"] = (
            merged["predicted_visits"] * (1.0 + merged["adjustment_signal"])
        ).clip(lower=0)
        merged["predicted_visits"] = merged["predicted_visits"].round().astype(int)

        return merged[["week_start", "week_end", "month_start", "predicted_visits"]]
