# California National Park Visitation Planner

## AI Build Specification

Version: **1.2**
Status: In Development

---

# 1. Objective

Build a full-stack web application that forecasts weekly crowd levels for California national parks and generates travel recommendations.

Supported parks:

* Yosemite
* Joshua Tree
* Death Valley
* Sequoia
* Kings Canyon

The system produces **26-week crowd forecasts** and identifies **optimal travel windows**.

---

# 2. Technology Stack

## Frontend

* Next.js
* TypeScript
* Tailwind
* Recharts
* Mapbox or Leaflet

## Backend

* FastAPI
* PostgreSQL
* Redis
* Pandas
* Prophet
* XGBoost
* Scikit-learn

---

# 3. Repository Structure

```
california-park-planner/

frontend/
  app/
  components/
  lib/
  types/

backend/
  app/
    api/
    models/
    services/
    jobs/
  tests/

data/
  raw/
  processed/
  fixtures/

docs/
  PRD.md
  AI_BUILD_SPEC.md

scripts/
```

---

# 4. Backend Responsibilities

The backend provides all forecasting and travel recommendation logic.

Responsibilities include:

* park metadata
* forecast generation
* best-week recommendations
* crowd calendar generation
* accessibility details
* alert aggregation
* scoring calculations

All responses are delivered via **FastAPI APIs**.

---

# 5. Required API Endpoints

### Park Metadata

```
GET /parks
```

Returns all parks.

---

### Map Data

```
GET /parks/map-data
```

Returns park markers and current crowd scores.

---

### Park Detail

```
GET /parks/{park_id}
```

Returns park metadata.

---

### Forecast

```
GET /parks/{park_id}/forecast
```

Returns **26-week forecast data**.

---

### Best Weeks

```
GET /parks/{park_id}/best-weeks
```

Returns:

* top 5 recommended weeks
* hidden gem weeks

---

### Crowd Calendar

```
GET /parks/{park_id}/calendar
```

Returns crowd calendar data.

---

### Accessibility Details

```
GET /parks/{park_id}/accessibility
```

Returns accessibility score breakdown.

---

### Alerts

```
GET /parks/{park_id}/alerts
```

Returns current alerts affecting park visits.

---

# 6. Forecasting Pipeline

The forecasting system uses **park-specific models**.

Each park maintains its own forecasting pipeline while sharing reusable feature engineering modules.

---

## Stage 1 — Baseline Time-Series Forecast

A **Prophet model** generates monthly baseline visitation forecasts.

Captures:

* seasonal cycles
* long-term visitation growth
* park-specific seasonal patterns

---

## Stage 2 — Weekly Disaggregation

Monthly visitation predictions are converted into **weekly forecasts**.

Methods include:

* normalized weekly allocation weights
* seasonal visitation patterns
* holiday adjustments

---

## Stage 3 — Machine Learning Adjustment

An **XGBoost model** adjusts baseline forecasts using external signals.

Features may include:

* Google Trends search interest
* Social Media Exposure (SME) index
* weather anomalies
* holiday proximity
* lagged visitation

---

# 7. ML Pipeline Directory Structure

Forecasting code should follow a modular structure to keep model logic maintainable.

```
backend/
  app/
    services/
      forecasting/
        __init__.py
        baseline_prophet.py
        weekly_disaggregation.py
        xgboost_adjustment.py
        feature_engineering.py
        forecast_runner.py
    jobs/
      etl_pipeline.py
      retrain_pipeline.py
      forecast_generation.py
```

---

## Module Responsibilities

### baseline_prophet.py

Responsible for baseline time-series forecasting.

Responsibilities:

* train Prophet models for each park
* load visitation history
* generate monthly baseline forecasts

---

### weekly_disaggregation.py

Converts monthly forecasts into weekly predictions.

Responsibilities:

* compute seasonal weekly weights
* ensure weights sum to monthly totals
* incorporate holiday distribution effects

---

### xgboost_adjustment.py

Adjusts baseline predictions using machine learning.

Responsibilities:

* load engineered features
* apply XGBoost adjustment
* incorporate trend signals

---

### feature_engineering.py

Generates forecasting features.

Features may include:

* lagged visitation
* rolling averages
* holiday proximity
* Google Trends index
* SME index
* weather anomalies

---

### forecast_runner.py

Coordinates the full forecast generation process.

Responsibilities:

1. run Prophet baseline
2. perform weekly disaggregation
3. apply ML adjustment
4. output weekly forecasts

---

# 8. Job Modules

### etl_pipeline.py

Handles data ingestion and normalization.

Responsibilities:

* load visitation datasets
* normalize weather inputs
* update feature tables

---

### retrain_pipeline.py

Handles scheduled retraining.

Responsibilities:

* retrain park-specific models
* update stored model artifacts

---

### forecast_generation.py

Generates forecasts used by the application.

Responsibilities:

* run forecast_runner
* generate 26-week forecasts
* write forecast outputs to database

---

# 9. Mock Data Requirement

Before external ETL pipelines are connected, the system must generate mock data.

Mock data must include:

* historical visitation records
* forecast weeks
* crowd scores
* weather scores
* alerts
* accessibility details

The application must run fully using mock data.

---

# 10. Frontend Components

The frontend should include the following reusable components.

* FeaturedInsightCards
* CaliforniaParkMap
* ParkMarker
* ParkSummaryPanel
* ForecastChart
* ScoreCard
* BestWeeksList
* HiddenGemBadge
* CrowdCalendar
* AccessibilityBreakdownModal
* AlertBanner

---

# 11. Cache Strategy

Redis should cache:

* parks
* map data
* forecast results
* best weeks
* crowd calendar

Refresh cadence:

* forecasts daily
* alerts every 6 hours

---

# 12. Testing

## Backend

Testing framework:

```
pytest
```

Tests should cover:

* scoring calculations
* hidden gem classification
* recommendation logic
* API endpoints

---

## Frontend

Testing frameworks:

* vitest
* jest

Focus areas:

* component rendering
* API integration
* UI state transitions

---

# 13. Development Order

1. initialize repository scaffold
2. implement database models
3. seed mock data
4. implement backend APIs
5. build homepage UI
6. build park dashboard
7. implement scoring logic
8. build forecast pipeline
9. add Redis caching
10. finalize testing

---

# 14. Definition of Done

V1 is complete when:

* all 5 parks supported
* homepage map works
* park dashboards render
* best weeks shown
* hidden gems shown
* crowd calendar works
* accessibility details clickable
* alerts visible
* tests pass
* forecast pipeline produces 26-week predictions
