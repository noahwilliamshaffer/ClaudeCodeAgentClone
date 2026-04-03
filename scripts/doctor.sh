#!/usr/bin/env bash
# Check Ollama connectivity (see: python3 -m agent doctor).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m agent doctor
