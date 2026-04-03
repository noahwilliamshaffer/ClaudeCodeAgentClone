#!/usr/bin/env bash
# Planning mode — structured plan only (no file writes from orchestrator).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
if [[ $# -lt 1 ]]; then
  echo "usage: $0 --task tasks/<name>.task.json" >&2
  exit 2
fi
exec python3 -m agent plan "$@"
