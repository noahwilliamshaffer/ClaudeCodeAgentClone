#!/usr/bin/env bash
# Explicit agent pipeline (see: python3 -m agent pipeline --help).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m agent pipeline "$@"
