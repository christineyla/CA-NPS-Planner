# California National Park Visitation Planner

Initial monorepo scaffold for a full-stack application that forecasts weekly crowd levels and helps users choose better park visit windows across California national parks.

## Repository Layout

```text
.
├── frontend/                # Next.js + TypeScript + Tailwind frontend
├── backend/                 # FastAPI backend service
├── data/
│   ├── raw/                 # Source datasets
│   ├── processed/           # Processed feature/forecast outputs
│   └── fixtures/            # Mock/seed fixtures
├── docs/                    # Product and build specifications
└── scripts/                 # Developer utility scripts
```

## Prerequisites

- Node.js 20+
- npm 10+
- Python 3.11+

## Quick Start

1. Copy environment templates:

   ```bash
   cp frontend/.env.example frontend/.env.local
   cp backend/.env.example backend/.env
   ```

2. Install dependencies:

   ```bash
   ./scripts/setup.sh
   ```

3. Start backend:

   ```bash
   cd backend
   source .venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. Start frontend (new terminal):

   ```bash
   cd frontend
   npm run dev
   ```

Frontend runs at `http://localhost:3000` and backend at `http://localhost:8000`.

## Developer Commands

### Frontend

```bash
cd frontend
npm run lint
npm run typecheck
npm run format
npm run test
```

### Backend

```bash
cd backend
source .venv/bin/activate
ruff check .
black --check .
pytest
```

### Seed Mock Backend Data

```bash
./scripts/seed-backend-db.sh
```

By default seeding uses `DATABASE_URL` from `backend/.env`; if unset it falls back to a local sqlite file (`backend/local.db`).

## Notes

- This commit intentionally contains only scaffolding and DX setup.
- Business logic, forecasting pipeline code, data ingestion, and feature endpoints will be implemented in later phases.
