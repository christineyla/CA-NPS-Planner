# California National Park Visitation Planner

## AI Build Specification

---

# 1. Objective

Build a full-stack web application that forecasts weekly crowd levels for California national parks and generates travel recommendations.

Supported parks:

* Yosemite
* Joshua Tree
* Death Valley
* Sequoia
* Kings Canyon

---

# 2. Technology Stack

Frontend

Next.js
TypeScript
Tailwind
Recharts
Mapbox or Leaflet

Backend

FastAPI
PostgreSQL
Redis
Pandas
Prophet
XGBoost
Scikit-learn

---

# 3. Repository Structure

california-park-planner/

frontend/

app
components
lib
types

backend/

app/

api
models
services
jobs

tests

data/

raw
processed
fixtures

docs/

PRD.md
AI_BUILD_SPEC.md

scripts/

---

# 4. Backend Responsibilities

Backend must provide:

* park metadata
* forecast data
* best weeks recommendations
* crowd calendar
* accessibility details
* alerts

All responses delivered via FastAPI.

---

# 5. Required API Endpoints

GET /parks

Returns all parks.

---

GET /parks/map-data

Returns park markers and crowd scores.

---

GET /parks/{park_id}

Returns park metadata.

---

GET /parks/{park_id}/forecast

Returns 26 week forecast.

---

GET /parks/{park_id}/best-weeks

Returns top 5 weeks and hidden gem weeks.

---

GET /parks/{park_id}/calendar

Returns crowd calendar data.

---

GET /parks/{park_id}/accessibility

Returns accessibility details.

---

GET /parks/{park_id}/alerts

Returns alerts.

---

# 6. Forecasting Pipeline

Stage 1

Prophet monthly forecast.

Stage 2

Convert monthly predictions to weekly.

Stage 3

Adjust weekly demand using XGBoost features.

Features include:

Google trends
weather anomalies
holiday proximity
lagged visits

---

# 7. Mock Data Requirement

Before ETL is connected the system must generate mock data for:

* historical visitation
* forecast weeks
* scores
* alerts
* accessibility details

The application should run fully with mock data.

---

# 8. Frontend Components

FeaturedInsightCards
CaliforniaParkMap
ParkMarker
ParkSummaryPanel
ForecastChart
ScoreCard
BestWeeksList
HiddenGemBadge
CrowdCalendar
AccessibilityBreakdownModal
AlertBanner

---

# 9. Cache Strategy

Redis should cache:

parks
map data
forecast results
best weeks
crowd calendar

Refresh:

forecasts daily
alerts every 6 hours

---

# 10. Testing

Backend:

pytest

Frontend:

vitest or jest

Test:

score calculations
hidden gem classification
API endpoints

---

# 11. Development Order

1. initialize repo scaffold
2. implement database models
3. seed mock data
4. implement backend APIs
5. build homepage UI
6. build park dashboard
7. implement scoring logic
8. build forecast pipeline
9. add Redis cache
10. add tests

---

# 12. Definition of Done

V1 complete when:

* all 5 parks supported
* homepage map works
* park dashboard renders
* best weeks shown
* hidden gems shown
* crowd calendar works
* accessibility details clickable
* alerts visible
* tests pass
