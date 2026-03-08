"""Daily forecast generation job that writes 26-week forecasts to the database."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import (
    Park,
    ParkTrendHistory,
    ParkVisitationForecast,
    ParkVisitationHistory,
    ParkWeatherHistory,
)
from app.services.forecasting import ForecastRunner
from app.services.scoring import (
    calculate_crowd_score,
    calculate_trip_score,
    calculate_weather_score,
)


@dataclass
class ForecastGenerationJob:
    """Generate park-specific 26-week forecasts and persist to forecast table."""

    forecast_runner: ForecastRunner = field(default_factory=ForecastRunner)

    def run(
        self,
        session: Session,
        horizon_weeks: int = 26,
        seed: int = 42,
    ) -> int:
        """Create forecast rows for all parks and return row count written."""

        parks = session.query(Park).order_by(Park.id.asc()).all()
        written_rows = 0

        for park in parks:
            monthly_history = self._load_monthly_history(session=session, park_id=park.id)
            if monthly_history.empty:
                continue

            trend_history = self._load_weekly_trend_history(session=session, park_id=park.id)
            weekly_forecasts = self.forecast_runner.run_for_park(
                park_id=park.id,
                monthly_history=monthly_history,
                horizon_weeks=horizon_weeks,
                seed=seed,
                weekly_trend_history=trend_history,
            )
            historical_weekly = self._approximate_historical_weekly(monthly_history)

            session.execute(
                delete(ParkVisitationForecast).where(ParkVisitationForecast.park_id == park.id)
            )
            weather_by_month = self._load_monthly_weather_by_month_start(
                session=session,
                park_id=park.id,
            )

            for _, row in weekly_forecasts.iterrows():
                weather_score = self._weather_score_for_week(
                    weather_by_month=weather_by_month,
                    month_start=row["month_start"],
                )
                crowd_score = calculate_crowd_score(
                    predicted_weekly_visits=int(row["predicted_visits"]),
                    historical_weekly_visits=historical_weekly,
                )
                trip_score = calculate_trip_score(
                    crowd_score=crowd_score,
                    weather_score=weather_score,
                    accessibility_score=park.accessibility_score,
                )
                forecast_record = ParkVisitationForecast(
                    park_id=park.id,
                    week_start=row["week_start"].date(),
                    week_end=row["week_end"].date(),
                    predicted_visits=int(row["predicted_visits"]),
                    crowd_score=crowd_score,
                    weather_score=weather_score,
                    accessibility_score=park.accessibility_score,
                    trip_score=trip_score,
                )
                session.add(forecast_record)
                written_rows += 1

        session.commit()
        return written_rows

    def _load_monthly_history(self, session: Session, park_id: int) -> pd.DataFrame:
        rows = (
            session.query(ParkVisitationHistory)
            .where(ParkVisitationHistory.park_id == park_id)
            .order_by(ParkVisitationHistory.observation_month.asc())
            .all()
        )
        return pd.DataFrame(
            {
                "month_start": [pd.Timestamp(row.observation_month) for row in rows],
                "visits": [row.visits for row in rows],
            }
        )

    def _load_weekly_trend_history(self, session: Session, park_id: int) -> pd.DataFrame:
        rows = (
            session.query(ParkTrendHistory)
            .where(ParkTrendHistory.park_id == park_id)
            .order_by(ParkTrendHistory.observation_date.asc())
            .all()
        )
        if not rows:
            return pd.DataFrame(columns=["week_start", "google_trends_index"])

        frame = pd.DataFrame(
            {
                "observation_date": [pd.Timestamp(row.observation_date) for row in rows],
                "google_trends_index": [row.google_trends_index for row in rows],
            }
        )
        frame["week_start"] = frame["observation_date"].dt.to_period("W-SUN").dt.start_time
        weekly = frame.groupby("week_start", as_index=False).agg(
            google_trends_index=("google_trends_index", "mean")
        )
        return weekly

    def _approximate_historical_weekly(self, monthly_history: pd.DataFrame) -> list[int]:
        return (monthly_history["visits"] / 4.345).round().astype(int).tolist()

    def _load_monthly_weather_by_month_start(
        self, session: Session, park_id: int
    ) -> dict[pd.Timestamp, tuple[float, float]]:
        rows = (
            session.query(ParkWeatherHistory)
            .where(ParkWeatherHistory.park_id == park_id)
            .order_by(ParkWeatherHistory.observation_date.asc())
            .all()
        )
        if not rows:
            return {}

        frame = pd.DataFrame(
            {
                "observation_date": [pd.Timestamp(row.observation_date) for row in rows],
                "avg_temp_f": [row.avg_temp_f for row in rows],
                "precipitation_mm": [row.precipitation_mm for row in rows],
            }
        )
        frame["month_start"] = frame["observation_date"].dt.to_period("M").dt.to_timestamp()
        monthly = (
            frame.groupby("month_start", as_index=False)
            .agg(avg_temp_f=("avg_temp_f", "mean"), precipitation_mm=("precipitation_mm", "mean"))
            .fillna({"precipitation_mm": 0.0})
        )
        return {
            row.month_start: (float(row.avg_temp_f), float(row.precipitation_mm))
            for row in monthly.itertuples(index=False)
        }

    def _weather_score_for_week(
        self,
        weather_by_month: dict[pd.Timestamp, tuple[float, float]],
        month_start: pd.Timestamp,
    ) -> float:
        monthly_weather = weather_by_month.get(pd.Timestamp(month_start))
        if monthly_weather is None:
            return calculate_weather_score(temperature_f=68.0, precipitation_probability=20)

        avg_temp_f, avg_precip_mm = monthly_weather
        precipitation_probability = max(0.0, min(100.0, avg_precip_mm * 10.0))
        return calculate_weather_score(
            temperature_f=avg_temp_f,
            precipitation_probability=precipitation_probability,
        )
