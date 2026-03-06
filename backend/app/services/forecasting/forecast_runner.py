"""Coordinator for the end-to-end forecast generation pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from app.services.forecasting.baseline_prophet import BaselineProphetForecaster
from app.services.forecasting.feature_engineering import FeatureEngineer
from app.services.forecasting.weekly_disaggregation import WeeklyDisaggregator
from app.services.forecasting.xgboost_adjustment import XGBoostAdjustmentLayer


@dataclass
class ForecastRunner:
    """Run baseline, disaggregation, and adjustment stages for a park."""

    baseline_forecaster: BaselineProphetForecaster = field(default_factory=BaselineProphetForecaster)
    disaggregator: WeeklyDisaggregator = field(default_factory=WeeklyDisaggregator)
    feature_engineer: FeatureEngineer = field(default_factory=FeatureEngineer)
    adjustment_layer: XGBoostAdjustmentLayer = field(default_factory=XGBoostAdjustmentLayer)

    def run_for_park(
        self,
        park_id: int,
        monthly_history: pd.DataFrame,
        seasonal_weights: dict[int, float] | None = None,
        holiday_weeks: set[pd.Timestamp] | None = None,
        horizon_weeks: int = 26,
        seed: int = 42,
    ) -> pd.DataFrame:
        """Generate a full 26-week forecast for a specific park."""

        monthly_forecast = self.baseline_forecaster.forecast_monthly(
            park_id=park_id,
            monthly_history=monthly_history,
            periods=max(6, (horizon_weeks // 4) + 1),
        )
        weekly_forecast = self.disaggregator.disaggregate(
            monthly_forecast=monthly_forecast,
            horizon_weeks=horizon_weeks,
            seasonal_weights=seasonal_weights,
            holiday_weeks=holiday_weeks,
            seed=seed,
        )
        feature_frame = self.feature_engineer.build_weekly_features(
            weekly_frame=weekly_forecast,
            holiday_weeks=holiday_weeks,
        )
        adjusted = self.adjustment_layer.adjust(
            weekly_forecast=weekly_forecast,
            feature_frame=feature_frame,
        )
        adjusted["park_id"] = park_id
        return adjusted[["park_id", "week_start", "week_end", "month_start", "predicted_visits"]]
