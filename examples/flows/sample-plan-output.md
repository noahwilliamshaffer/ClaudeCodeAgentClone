# Sample planner output (illustrative)

The planner writes two artifacts under `memory/plans/`:

- `<task-id>.plan.json` — machine-readable plan for the executor.
- `<task-id>.plan.md` — human-readable summary.

## Example `steps` entry

```json
{
  "title": "Add health check helper",
  "intent": "Implement a minimal HTTP GET to Ollama /api/tags from stdlib.",
  "mode": "write",
  "risk": "low",
  "validation": "python3 -m compileall -q agent"
}
```

## Safe iteration

1. Run planning only: `./scripts/plan.sh --task tasks/example-feature.task.json`
2. Inspect `memory/plans/*.plan.md`
3. Execute step 0 dry-run: `./scripts/execute.sh --task ... --plan ... --step 0`
4. Apply changes: add `--force-execute` when you accept the proposed diff narrative
