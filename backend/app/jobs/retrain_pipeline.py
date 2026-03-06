"""Scheduled park-specific model retraining workflow."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.jobs.etl_pipeline import ETLPipeline
from app.services.forecasting import BaselineProphetForecaster


@dataclass
class RetrainPipeline:
    """Retrain monthly baseline models for all configured parks."""

    etl_pipeline: ETLPipeline = field(default_factory=ETLPipeline)
    baseline_forecaster: BaselineProphetForecaster = field(default_factory=BaselineProphetForecaster)

    def run(self, park_ids: list[int], months: int = 120) -> dict[int, object]:
        """Train/retrain all park model states and return trained model map."""

        models: dict[int, object] = {}
        for park_id in park_ids:
            monthly_history = self.etl_pipeline.run(park_id=park_id, months=months)
            model = self.baseline_forecaster.train_or_load(
                park_id=park_id,
                monthly_history=monthly_history,
            )
            models[park_id] = model
        return models
