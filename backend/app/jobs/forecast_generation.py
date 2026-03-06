"""Daily forecast generation job that writes 26-week forecasts to the database."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import Park, ParkVisitationForecast, ParkVisitationHistory
from app.services.forecasting import ForecastRunner
from app.services.scoring import calculate_crowd_score, calculate_trip_score, calculate_weather_score


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

            weekly_forecasts = self.forecast_runner.run_for_park(
                park_id=park.id,
                monthly_history=monthly_history,
                horizon_weeks=horizon_weeks,
                seed=seed,
            )
            historical_weekly = self._approximate_historical_weekly(monthly_history)

            session.execute(delete(ParkVisitationForecast).where(ParkVisitationForecast.park_id == park.id))

            for _, row in weekly_forecasts.iterrows():
                weather_score = calculate_weather_score(temperature_f=68.0, precipitation_probability=20)
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

    def _approximate_historical_weekly(self, monthly_history: pd.DataFrame) -> list[int]:
        return (monthly_history["visits"] / 4.345).round().astype(int).tolist()
