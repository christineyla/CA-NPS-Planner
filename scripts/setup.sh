#!/usr/bin/env bash
set -euo pipefail

echo "Setting up frontend dependencies..."
(
  cd frontend
  npm install
)

echo "Setting up backend virtual environment and dependencies..."
(
  cd backend
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
)

echo "Setup complete."
