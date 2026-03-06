#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../backend"

if [ -d ".venv" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

python -m scripts.seed_db
