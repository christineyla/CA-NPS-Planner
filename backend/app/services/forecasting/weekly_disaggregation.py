"""Convert monthly predictions to week-level forecasts."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class WeeklyDisaggregator:
    """Allocate monthly visitation totals into weekly totals with deterministic weights."""

    holiday_weight_boost: float = 0.2

    def _weekly_boundaries(self, start_date: pd.Timestamp, horizon_weeks: int) -> pd.DataFrame:
        weeks = pd.date_range(start=start_date, periods=horizon_weeks, freq="W-MON")
        boundaries = pd.DataFrame({"week_start": weeks})
        boundaries["week_end"] = boundaries["week_start"] + pd.Timedelta(days=6)
        boundaries["month_start"] = boundaries["week_start"].values.astype("datetime64[M]")
        return boundaries

    def disaggregate(
        self,
        monthly_forecast: pd.DataFrame,
        horizon_weeks: int = 26,
        seasonal_weights: dict[int, float] | None = None,
        holiday_weeks: set[pd.Timestamp] | None = None,
        seed: int = 42,
    ) -> pd.DataFrame:
        """Convert monthly predictions to weekly values while preserving monthly totals."""

        del seed  # deterministic by construction
        seasonal_weights = seasonal_weights or {}
        holiday_weeks = holiday_weeks or set()

        start_date = monthly_forecast["month_start"].min()
        weekly = self._weekly_boundaries(start_date=start_date, horizon_weeks=horizon_weeks)

        monthly_lookup = monthly_forecast.set_index("month_start")["predicted_visits"].to_dict()
        weekly["monthly_total"] = weekly["month_start"].map(monthly_lookup).fillna(0).astype(float)

        base_weight = 1.0
        weekly["weight"] = base_weight
        weekly["weight"] *= weekly["month_start"].dt.month.map(lambda month: seasonal_weights.get(month, 1.0))
        weekly["weight"] *= weekly["week_start"].map(
            lambda dt: 1.0 + self.holiday_weight_boost if dt in holiday_weeks else 1.0
        )

        normalized_parts: list[pd.DataFrame] = []
        for month_start, month_group in weekly.groupby("month_start", sort=True):
            group = month_group.copy()
            group_weight_sum = group["weight"].sum()
            if group_weight_sum <= 0:
                group["normalized_weight"] = 1.0 / len(group)
            else:
                group["normalized_weight"] = group["weight"] / group_weight_sum

            target_month_total = monthly_lookup.get(month_start, 0)
            group["predicted_visits"] = target_month_total * group["normalized_weight"]

            if len(group) > 0:
                rounded = group["predicted_visits"].round().astype(int)
                rounding_error = int(target_month_total - rounded.sum())
                if rounding_error != 0:
                    rounded.iloc[-1] += rounding_error
                group["predicted_visits"] = rounded

            normalized_parts.append(group)

        result = pd.concat(normalized_parts, ignore_index=True)
        return result[["week_start", "week_end", "month_start", "predicted_visits"]]
