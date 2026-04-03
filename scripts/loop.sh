#!/usr/bin/env bash
# Full loop: plan → all executor steps → review (optional validate).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m agent loop "$@"
