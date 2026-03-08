# California National Park Visitation Planner

Full-stack monorepo for forecasting California national park crowd levels and surfacing better trip windows.

## Repository Layout

```text
.
├── frontend/                # Next.js + TypeScript + Tailwind frontend
├── backend/                 # FastAPI backend service
├── data/
│   ├── raw/                 # Source datasets
│   ├── processed/           # Processed feature/forecast outputs
│   └── fixtures/            # Mock/seed fixtures
├── docs/                    # Product/build/task specs
└── scripts/                 # Local developer utility scripts
```

## Prerequisites

- Node.js 20+
- npm 10+
- Python 3.11+
- PostgreSQL 15+ (recommended for parity)
- Redis 7+ (for API response caching)

## 1) Environment Setup

Copy environment templates:

```bash
cp frontend/.env.example frontend/.env.local
cp backend/.env.example backend/.env
```

Install all dependencies:

```bash
./scripts/setup.sh
```

## 2) Start Local Infra

You can run Postgres + Redis locally via native installs, or with Docker:

```bash
docker run --name ca-nps-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=ca_nps_planner -p 5432:5432 -d postgres:15

docker run --name ca-nps-redis -p 6379:6379 -d redis:7
```

`backend/.env.example` already includes compatible defaults:

- `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ca_nps_planner`
- `REDIS_URL=redis://localhost:6379/0`
- `REDIS_CACHE_TTL_SECONDS=300`

If Redis is unavailable, APIs continue to work without cached responses.

### Python dependency note (local dev)

`backend/requirements.txt` intentionally omits `psycopg2-binary` so local setup on newer Python
versions (including Python 3.13) is not blocked by PostgreSQL driver wheel availability when
developing against SQLite/in-memory tests.

For production or local PostgreSQL parity, install an explicit Postgres driver in your runtime
environment (for example `psycopg[binary]` or `psycopg2-binary`) and keep it pinned in deployment
configuration.

## 3) Seed Mock Data

Run the backend seed script:

```bash
./scripts/seed-backend-db.sh
```

This loads parks, forecast weeks, crowd calendar records, accessibility fields, and alerts.

## 4) Load Real NPS Visitation History (Initial ETL Layer)

After seeding, load real monthly visitation history for the five in-scope parks:

```bash
./scripts/load-visitation-etl.sh
```

The ETL preserves an official-source strategy and downloads monthly recreation visits from IRMA first. If the IRMA direct download endpoint returns an HTTP error (including 500 responses), it automatically falls back to Data.gov by resolving the official dataset titled `NPS Visitor Use Statistics Data Package, 2024` (first via known CKAN slugs, then via `package_search` title match) and selecting the main visitation CSV resource (preferencing `Main_Data.csv`/main-data style resources). Then it:

- filters to Yosemite, Joshua Tree, Death Valley, Sequoia, and Kings Canyon
- normalizes records into `park_visitation_history`
- applies an initial rolling 3-year historical window
- avoids preliminary current-year assumptions by loading only published package data
- writes ETL metadata fields: `data_source`, `source_updated_at` (if inferable from source package), and `ingested_at`
- safely reruns by replacing the same park/month window to prevent duplicates
- raises a clear error if both official IRMA and Data.gov sources fail

Seeded mock data remains in place for domains (alerts and other optional external signals) that are not yet sourced by live ETL.


## 4b) Load Real Meteostat Weather History (Point Daily ETL)

After seeding, load real daily weather history for the same five in-scope parks:

```bash
./scripts/load-weather-etl.sh
```

This ETL uses **Meteostat Point Daily** (`meteostat.Daily` for a `meteostat.Point`) and requests daily observations by representative park latitude/longitude (with optional altitude). It then:

- queries the last rolling 3-year historical window (`start = Jan 1 of (latest_year - 2)`, `end = yesterday`)
- maps the resulting rows to internal park IDs for Yosemite, Joshua Tree, Death Valley, Sequoia, and Kings Canyon
- stores daily weather in `park_weather_history` with:
  - `observation_date`
  - `avg_temp_f`
  - `min_temp_f`
  - `max_temp_f`
  - `precipitation_mm`
- writes ETL metadata fields: `data_source`, `source_updated_at`, and `ingested_at`
- safely reruns by replacing overlapping park/day records in-window to prevent duplicates

### Meteostat source timestamp assumption

Meteostat Point Daily does not provide a clear dataset-level `source_updated_at` timestamp in query responses. Current behavior:

- store `source_updated_at` when explicitly provided by the ETL caller
- otherwise persist `NULL` and rely on `ingested_at` as the local load timestamp

### Fallback behavior

Seeded/mock weather behavior remains available wherever real weather rows are not yet present (for example, weather scoring falls back to the existing default assumptions when a forecast month has no weather history).

## 4c) Load Google Trends History (3-year Weekly ETL)

After seeding, load Google Trends search-interest history for the same five in-scope parks:

```bash
./scripts/load-trends-etl.sh
```

Trend query mapping is centrally configured in `IN_SCOPE_PARK_TREND_QUERIES` and currently uses one query per park:

- `Yosemite National Park`
- `Joshua Tree National Park`
- `Death Valley National Park`
- `Sequoia National Park`
- `Kings Canyon National Park`

Provider strategy is pluggable:

- **Official provider path**: used when `GOOGLE_TRENDS_API_URL` and `GOOGLE_TRENDS_API_TOKEN` are configured.
- **Fallback provider path (local/dev)**: uses `pytrends` (unofficial Google Trends client).

The ETL ingests a rolling 3-year window and prefers weekly points. It then stores rows in `park_trend_history` with:

- `park_id`
- `observation_date`
- `google_trends_index`
- `data_source`
- `source_updated_at`
- `ingested_at`

### Important normalization note

Google Trends values are **normalized relative trend scores** (typically on a 0-100 index within the selected query/timeframe), not absolute search counts.

### Timestamp assumptions

- `source_updated_at` is stored if the selected provider exposes a source-level update timestamp.
- If unavailable (common for the fallback pytrends path), `source_updated_at` is `NULL` and `ingested_at` is used as the local ETL timestamp.

### Forecast integration behavior

Forecast generation consumes trend history when present and continues to use existing fallback behavior when trend rows are unavailable for a park/week.

## 4d) Generate Forecasts + Refresh Crowd Calendar

After running visitation, weather, and trends ETLs, regenerate forecasts for all five in-scope parks:

```bash
./scripts/run-forecast-generation.sh
```

This forecast run:

- loads the latest monthly visitation history for each park
- uses weather and trends history when present
- preserves fallback behavior when weather/trends are missing
- replaces each park forecast window in `park_visitation_forecast` on rerun (duplicate-safe)
- refreshes `crowd_calendar` rows from the newly written forecasts
- writes forecast metadata fields (`forecast_generated_at`, `model_trained_at`, `data_cutoff_date`, `model_version`)

### Recommended local execution order

```bash
./scripts/seed-backend-db.sh
./scripts/load-visitation-etl.sh
./scripts/load-weather-etl.sh
./scripts/load-trends-etl.sh
./scripts/run-forecast-generation.sh
```

## 5) Run the App End-to-End

Backend:

```bash
./scripts/run-backend.sh
```

Frontend (new terminal):

```bash
./scripts/run-frontend.sh
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Health endpoint: http://localhost:8000/health

## 6) Testing and Quality Commands

Run backend checks:

```bash
./scripts/test-backend.sh
```

Run backend lint/format checks:

```bash
./scripts/lint-backend.sh
```

Run frontend checks:

```bash
./scripts/test-frontend.sh
```

Run full test suite:

```bash
./scripts/test-all.sh
```

You can also run commands manually:

### Frontend

```bash
cd frontend
npm run lint
npm run typecheck
npm run test -- --run
```

### Backend

```bash
cd backend
source .venv/bin/activate
python3 -m pytest
```

## Production-Readiness Notes (Current Phase)

- Redis-backed caching is enabled for high-read park endpoints (`/parks`, `/parks/map-data`, park detail, forecast, best-weeks, calendar, accessibility, alerts).
- API error handling now returns consistent payloads for validation, database, and unexpected server exceptions.
- Local scripts are included for setup, seeding, running, and testing to improve developer onboarding and repeatability.
