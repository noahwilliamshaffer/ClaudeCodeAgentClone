# Sample planner output

Running:

```bash
./scripts/plan.sh --task tasks/example-feature.task.json
```

writes two artifacts under `memory/plans/`:

| File | Contents |
|------|----------|
| `example-feature-001.plan.json` | Machine-readable plan for the executor |
| `example-feature-001.plan.md` | Human-readable phases, steps, and risks |

## Example step object (JSON)

```json
{
  "title": "Add Ollama health check to doctor output",
  "intent": "Surface model tags and base URL in JSON for scripting.",
  "mode": "write",
  "risk": "low",
  "validation": "python3 -m compileall -q agent"
}
```

## Safe iteration

1. Run planning only: `./scripts/plan.sh --task tasks/example-feature.task.json`
2. Open `memory/plans/example-feature-001.plan.md` and confirm scope
3. Execute step 0 in dry-run (default):

```bash
./scripts/execute.sh \
  --task tasks/example-feature.task.json \
  --plan memory/plans/example-feature-001.plan.json \
  --step 0
```

4. Apply changes only after review: add `--force-execute` (and optionally `--validate-after`)
