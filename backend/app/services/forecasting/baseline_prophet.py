"""Park-specific monthly baseline visitation forecasting via Prophet."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

try:
    from prophet import Prophet
except Exception:  # pragma: no cover - fallback supports environments without compiled deps
    Prophet = None  # type: ignore[assignment]


@dataclass
class BaselineProphetForecaster:
    """Train or load park-specific baseline models with Prophet-first behavior."""

    seed: int = 42
    _park_models: dict[int, object] = field(default_factory=dict)
    min_training_months: int = 24

    def _normalized_history(self, monthly_history: pd.DataFrame) -> pd.DataFrame:
        ordered = monthly_history.sort_values("month_start").reset_index(drop=True).copy()
        ordered["month_start"] = ordered["month_start"].dt.to_period("M").dt.to_timestamp()
        normalized = (
            ordered.groupby("month_start", as_index=False)
            .agg(visits=("visits", "sum"))
            .sort_values("month_start")
            .reset_index(drop=True)
        )
        normalized["visits"] = pd.to_numeric(normalized["visits"], errors="coerce")
        normalized = normalized.dropna(subset=["month_start", "visits"])
        return normalized[normalized["visits"] >= 0].reset_index(drop=True)

    def _training_frame(self, monthly_history: pd.DataFrame) -> pd.DataFrame:
        ordered = self._normalized_history(monthly_history)
        if len(ordered) > self.min_training_months:
            ordered = ordered.tail(self.min_training_months)

        training = ordered.rename(columns={"month_start": "ds", "visits": "y"})[["ds", "y"]]
        training["ds"] = pd.to_datetime(training["ds"], errors="coerce")
        training["y"] = pd.to_numeric(training["y"], errors="coerce")
        return training.dropna(subset=["ds", "y"]).sort_values("ds").reset_index(drop=True)

    def _build_fallback_model_state(self, ordered_history: pd.DataFrame) -> dict[str, float | dict[int, float]]:
        y = ordered_history["visits"].astype(float)
        slope = float((y.iloc[-1] - y.iloc[0]) / max(len(y) - 1, 1))
        level = float(max(1.0, y.mean()))
        seasonal = (
            ordered_history.groupby(ordered_history["month_start"].dt.month)["visits"].mean() / level
        ).to_dict()
        return {
            "last_value": float(max(1.0, y.iloc[-1])),
            "slope": slope,
            "level": level,
            "seasonality_default": 1.0,
            "seasonality_values": seasonal,
        }

    def _fallback_forecast(self, park_id: int, ordered_history: pd.DataFrame, periods: int) -> pd.DataFrame:
        model = self._build_fallback_model_state(ordered_history)
        start_month = ordered_history["month_start"].max() + pd.offsets.MonthBegin(1)
        months = pd.date_range(start=start_month, periods=periods, freq="MS")
        rows: list[dict[str, float | pd.Timestamp]] = []
        for idx, month_start in enumerate(months, start=1):
            seasonal = model["seasonality_values"].get(
                month_start.month,
                model["seasonality_default"],
            )
            trend_projection = max(1.0, model["last_value"] + model["slope"] * idx)
            seasonal_multiplier = max(0.2, float(seasonal))
            yhat = max(1.0, 0.65 * trend_projection + 0.35 * (model["level"] * seasonal_multiplier))
            rows.append(
                {
                    "month_start": month_start,
                    "park_id": park_id,
                    "predicted_visits": int(round(yhat)),
                }
            )

        return pd.DataFrame(rows)

    def train_or_load(self, park_id: int, monthly_history: pd.DataFrame) -> object:
        """Train or return a cached model object for a specific park."""

        if park_id in self._park_models:
            return self._park_models[park_id]

        ordered = self._training_frame(monthly_history).rename(columns={"ds": "month_start", "y": "visits"})
        if ordered.empty or len(ordered) < 2:
            raise ValueError("Monthly visitation history must contain at least 2 valid rows")
        if Prophet is not None:
            prophet_frame = ordered.rename(columns={"month_start": "ds", "visits": "y"})[["ds", "y"]]
            model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
            model.fit(prophet_frame)
            self._park_models[park_id] = model
            return model
        model_state = self._build_fallback_model_state(ordered)
        self._park_models[park_id] = model_state
        return model_state

    def forecast_monthly(
        self,
        park_id: int,
        monthly_history: pd.DataFrame,
        periods: int = 6,
    ) -> pd.DataFrame:
        """Generate monthly forecast rows for a park."""

        ordered = self._normalized_history(monthly_history)
        if len(ordered) > self.min_training_months:
            ordered = ordered.tail(self.min_training_months).reset_index(drop=True)
        model = self.train_or_load(park_id=park_id, monthly_history=ordered)
        start_month = ordered["month_start"].max() + pd.offsets.MonthBegin(1)

        if Prophet is not None and hasattr(model, "make_future_dataframe"):
            future = model.make_future_dataframe(periods=periods, freq="MS", include_history=False)
            forecast = model.predict(future)
            result = forecast[["ds", "yhat"]].rename(columns={"ds": "month_start", "yhat": "predicted_visits"})
            result["predicted_visits"] = result["predicted_visits"].clip(lower=0).round().astype(int)
            result["park_id"] = park_id
            history_std = float(ordered["visits"].std(ddof=0))
            forecast_std = float(result["predicted_visits"].std(ddof=0))
            if result["predicted_visits"].max() > 0 and (forecast_std > 0 or history_std == 0):
                return result[["month_start", "park_id", "predicted_visits"]]

        return self._fallback_forecast(park_id=park_id, ordered_history=ordered, periods=periods)
