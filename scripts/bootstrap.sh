#!/usr/bin/env bash
# Verify prerequisites and print configuration hints.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=lib.sh
source "$ROOT/scripts/lib.sh"

echo "== Local agent workspace bootstrap =="
echo "ROOT=$ROOT"

require_cmd python3
python3 --version

if command -v ollama >/dev/null 2>&1; then
  echo "ollama: $(command -v ollama)"
  ollama --version 2>/dev/null || true
else
  echo "warn: ollama not found in PATH (install from https://ollama.com)" >&2
fi

if command -v opencode >/dev/null 2>&1; then
  echo "opencode: $(command -v opencode)"
  opencode --version 2>/dev/null || true
else
  echo "warn: opencode not found in PATH (optional for interactive runs)" >&2
fi

mkdir -p "$ROOT/logs" "$ROOT/memory/plans" "$ROOT/logs/backups"

echo ""
echo "Python smoke test (import agent package):"
PYTHONPATH="$ROOT" python3 -c "import agent; print('agent package OK:', agent.__version__)"

echo ""
if PYTHONPATH="$ROOT" python3 -c "import pytest" 2>/dev/null; then
  echo "Running pytest (tests/):"
  PYTHONPATH="$ROOT" python3 -m pytest "$ROOT/tests/" -q
else
  echo "pytest not installed; skip tests. Install with: pip install -r requirements-dev.txt"
fi

echo ""
echo "Next:"
echo "  1) ollama serve   # if not already running"
echo "  2) ollama pull llama3.2 && ollama pull qwen2.5-coder"
echo "  3) ./scripts/plan.sh --task tasks/example-feature.task.json"
echo "  4) ./scripts/sample-secure-refactor-plan.sh   # security / refactor analysis sample"
