#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR/backend"

if [[ ! -d ".venv" ]]; then
  echo "Backend virtual environment not found at backend/.venv"
  echo "Run ./scripts/setup.sh first."
  exit 1
fi

source .venv/bin/activate
python3 scripts/run_forecast_generation.py
