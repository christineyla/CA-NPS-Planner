#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../frontend"

npm run lint
npm run typecheck
npm run test -- --run --passWithNoTests
