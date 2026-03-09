"""Coordinator for the end-to-end forecast generation pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from app.services.forecasting.baseline_prophet import BaselineProphetForecaster
from app.services.forecasting.feature_engineering import FeatureEngineer
from app.services.forecasting.weekly_disaggregation import WeeklyDisaggregator
from app.services.forecasting.xgboost_adjustment import XGBoostAdjustmentLayer


@dataclass
class ForecastRunner:
    """Run baseline, disaggregation, and adjustment stages for a park."""

    baseline_forecaster: BaselineProphetForecaster = field(
        default_factory=BaselineProphetForecaster
    )
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
        weekly_trend_history: pd.DataFrame | None = None,
        forecast_start_date: date | pd.Timestamp | None = None,
    ) -> pd.DataFrame:
        """Generate a full 26-week forecast for a specific park."""

        normalized_history = monthly_history.copy()
        normalized_history["month_start"] = pd.to_datetime(normalized_history["month_start"])
        last_history_month = normalized_history["month_start"].max().to_period("M").to_timestamp()
        disaggregation_start = (
            pd.Timestamp(forecast_start_date) if forecast_start_date is not None else None
        )
        start_month = (
            disaggregation_start.to_period("M").to_timestamp()
            if disaggregation_start is not None
            else (last_history_month + pd.offsets.MonthBegin(1))
        )
        month_gap = max(
            0,
            (start_month.year - last_history_month.year) * 12
            + (start_month.month - last_history_month.month)
            - 1,
        )
        horizon_months = max(6, (horizon_weeks // 4) + 1)
        monthly_periods = month_gap + horizon_months

        monthly_forecast = self.baseline_forecaster.forecast_monthly(
            park_id=park_id,
            monthly_history=normalized_history,
            periods=monthly_periods,
        )
        weekly_forecast = self.disaggregator.disaggregate(
            monthly_forecast=monthly_forecast,
            horizon_weeks=horizon_weeks,
            start_date=disaggregation_start,
            seasonal_weights=seasonal_weights,
            holiday_weeks=holiday_weeks,
            seed=seed,
        )
        if weekly_trend_history is not None and not weekly_trend_history.empty:
            weekly_forecast = weekly_forecast.merge(
                weekly_trend_history[["week_start", "google_trends_index"]],
                on="week_start",
                how="left",
            )

        feature_frame = self.feature_engineer.build_weekly_features(
            weekly_frame=weekly_forecast,
            holiday_weeks=holiday_weeks,
        )
        adjusted = self.adjustment_layer.adjust(
            weekly_forecast=weekly_forecast.drop(columns=["google_trends_index"], errors="ignore"),
            feature_frame=feature_frame,
        )
        adjusted["park_id"] = park_id
        return adjusted[["park_id", "week_start", "week_end", "month_start", "predicted_visits"]]
