#!/usr/bin/env bash
# OpenCode adapter — runs a prompt through `opencode run` with project config.
# Usage: ./scripts/opencode-run.sh "your prompt here"
# Optional: OPENCODE_RUNTIME=1 is used by Python adapter when wrapping OpenCode (see docs).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v opencode >/dev/null 2>&1; then
  echo "error: opencode not found in PATH" >&2
  exit 127
fi

MODEL_LINE="$(
  python3 -c "import json, pathlib; print(json.loads(pathlib.Path('$ROOT/opencode.json').read_text(encoding='utf-8'))['model'])" 2>/dev/null \
    || echo "ollama/qwen2.5-coder:latest"
)"

exec opencode run -m "$MODEL_LINE" "$@"
