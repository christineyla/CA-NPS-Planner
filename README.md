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

Seeded mock data remains in place for other domains (weather/trends/alerts) that are not yet sourced by live ETL.

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
