#!/usr/bin/env bash
# Sample: run the secure refactor analysis task (planning only — no file writes from executor).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

echo "== Sample: analyze repo and propose a secure refactor plan =="
echo "Prerequisites: ollama serve, models from config/models.json pulled"
echo ""

python3 -m agent doctor

echo ""
echo "Running planner with tasks/secure-refactor-analysis.task.json ..."
python3 -m agent plan --task tasks/secure-refactor-analysis.task.json

echo ""
echo "Done. Inspect:"
echo "  - memory/plans/secure-refactor-analysis-001.plan.md"
echo "  - memory/plans/secure-refactor-analysis-001.plan.json"
