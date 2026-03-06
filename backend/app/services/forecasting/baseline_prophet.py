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

    def train_or_load(self, park_id: int, monthly_history: pd.DataFrame) -> object:
        """Train or return a cached model object for a specific park."""

        if park_id in self._park_models:
            return self._park_models[park_id]

        ordered = monthly_history.sort_values("month_start").reset_index(drop=True)
        if Prophet is not None:
            prophet_frame = ordered.rename(columns={"month_start": "ds", "visits": "y"})[["ds", "y"]]
            model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
            model.fit(prophet_frame)
            self._park_models[park_id] = model
            return model

        y = ordered["visits"].astype(float)
        slope = float((y.iloc[-1] - y.iloc[0]) / max(len(y) - 1, 1))
        seasonal = ordered.groupby(ordered["month_start"].dt.month)["visits"].mean().to_dict()
        model_state = {
            "last_value": float(y.iloc[-1]),
            "slope": slope,
            "seasonality_default": float(y.mean()),
            "seasonality_values": seasonal,
        }
        self._park_models[park_id] = model_state
        return model_state

    def forecast_monthly(
        self,
        park_id: int,
        monthly_history: pd.DataFrame,
        periods: int = 6,
    ) -> pd.DataFrame:
        """Generate monthly forecast rows for a park."""

        model = self.train_or_load(park_id=park_id, monthly_history=monthly_history)
        start_month = monthly_history["month_start"].max() + pd.offsets.MonthBegin(1)

        if Prophet is not None and hasattr(model, "make_future_dataframe"):
            future = model.make_future_dataframe(periods=periods, freq="MS", include_history=False)
            forecast = model.predict(future)
            result = forecast[["ds", "yhat"]].rename(columns={"ds": "month_start", "yhat": "predicted_visits"})
            result["predicted_visits"] = result["predicted_visits"].clip(lower=0).round().astype(int)
            result["park_id"] = park_id
            return result[["month_start", "park_id", "predicted_visits"]]

        months = pd.date_range(start=start_month, periods=periods, freq="MS")
        rows: list[dict[str, float | pd.Timestamp]] = []
        for idx, month_start in enumerate(months, start=1):
            seasonal = model["seasonality_values"].get(
                month_start.month,
                model["seasonality_default"],
            )
            trend_projection = model["last_value"] + model["slope"] * idx
            yhat = max(0.0, 0.6 * trend_projection + 0.4 * float(seasonal))
            rows.append(
                {
                    "month_start": month_start,
                    "park_id": park_id,
                    "predicted_visits": int(round(yhat)),
                }
            )

        return pd.DataFrame(rows)
