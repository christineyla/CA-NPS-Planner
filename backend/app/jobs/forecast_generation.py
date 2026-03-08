"""Daily forecast generation job that writes 26-week forecasts to the database."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone

import pandas as pd
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import (
    CrowdCalendar,
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
    model_version: str = "forecast-pipeline-v1"

    def run(
        self,
        session: Session,
        horizon_weeks: int = 26,
        seed: int = 42,
        generated_at: datetime | None = None,
        model_trained_at: datetime | None = None,
    ) -> int:
        """Create forecast rows for all parks and return row count written."""

        run_generated_at = generated_at or datetime.now(timezone.utc)
        run_model_trained_at = model_trained_at or run_generated_at
        run_context_date = run_generated_at.date()

        parks = session.query(Park).order_by(Park.id.asc()).all()
        written_rows = 0

        for park in parks:
            monthly_history = self._load_monthly_history(session=session, park_id=park.id)
            if monthly_history.empty:
                continue

            trend_history = self._load_weekly_trend_history(session=session, park_id=park.id)
            weather_by_month = self._load_monthly_weather_by_month_start(
                session=session,
                park_id=park.id,
            )
            data_cutoff_date = self._derive_data_cutoff_date(
                monthly_history=monthly_history,
                weather_by_month=weather_by_month,
                trend_history=trend_history,
            )
            forecast_start_date = self._derive_forecast_start_date(
                data_cutoff_date=data_cutoff_date,
                run_context_date=run_context_date,
            )
            weekly_forecasts = self.forecast_runner.run_for_park(
                park_id=park.id,
                monthly_history=monthly_history,
                horizon_weeks=horizon_weeks,
                seed=seed,
                weekly_trend_history=trend_history,
                forecast_start_date=forecast_start_date,
            )
            historical_weekly = self._approximate_historical_weekly(monthly_history)

            session.execute(delete(CrowdCalendar).where(CrowdCalendar.park_id == park.id))
            session.execute(
                delete(ParkVisitationForecast).where(ParkVisitationForecast.park_id == park.id)
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
                    forecast_generated_at=run_generated_at,
                    model_trained_at=run_model_trained_at,
                    data_cutoff_date=data_cutoff_date,
                    model_version=self.model_version,
                )
                session.add(forecast_record)
                written_rows += 1

            session.flush()
            self._refresh_crowd_calendar_for_park(session=session, park_id=park.id)

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


    def _derive_forecast_start_date(
        self,
        data_cutoff_date: date,
        run_context_date: date,
    ) -> date:
        cutoff_ts = pd.Timestamp(data_cutoff_date)
        run_context_ts = pd.Timestamp(run_context_date)
        current_week_start = run_context_ts - pd.Timedelta(days=run_context_ts.weekday())
        next_week_after_cutoff = cutoff_ts + pd.offsets.Week(weekday=0)
        forecast_start = max(current_week_start, next_week_after_cutoff)
        return forecast_start.date()

    def _derive_data_cutoff_date(
        self,
        monthly_history: pd.DataFrame,
        weather_by_month: dict[pd.Timestamp, tuple[float, float]],
        trend_history: pd.DataFrame,
    ) -> date:
        latest_visitation = monthly_history["month_start"].max().date()
        candidate_dates: list[date] = [latest_visitation]

        if weather_by_month:
            candidate_dates.append(max(weather_by_month.keys()).date())

        if not trend_history.empty:
            candidate_dates.append(trend_history["week_start"].max().date())

        return max(candidate_dates)

    def _refresh_crowd_calendar_for_park(self, session: Session, park_id: int) -> None:
        forecasts = (
            session.query(ParkVisitationForecast)
            .where(ParkVisitationForecast.park_id == park_id)
            .order_by(ParkVisitationForecast.week_start.asc())
            .all()
        )

        for forecast in forecasts:
            level, color = self._crowd_level(forecast.crowd_score)
            session.add(
                CrowdCalendar(
                    park_id=park_id,
                    forecast_id=forecast.id,
                    crowd_level=level,
                    color_hex=color,
                    crowd_score=forecast.crowd_score,
                )
            )

    def _crowd_level(self, crowd_score: float) -> tuple[str, str]:
        if crowd_score <= 30:
            return "low", "#16A34A"
        if crowd_score <= 60:
            return "moderate", "#EAB308"
        if crowd_score <= 80:
            return "busy", "#F97316"
        return "extreme", "#DC2626"
