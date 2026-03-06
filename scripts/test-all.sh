#!/usr/bin/env bash
set -euo pipefail

"$(dirname "$0")/test-backend.sh"
"$(dirname "$0")/test-frontend.sh"
