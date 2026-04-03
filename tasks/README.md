# Tasks

Tasks are JSON files consumed by the orchestrator (`python3 -m agent plan|execute|loop|...`).

## Fields

| Field | Description |
|-------|-------------|
| `id` | Stable identifier (used for plan filenames under `memory/plans/`) |
| `title` | Short title |
| `description` | Goal, acceptance criteria, and constraints for the model |
| `skill` | Skill id: basename of a file in `/skills` without `.md` |
| `planner_prompt` | Optional: filename in `/prompts` (default `planner.md`). Use `planner.secure-refactor.md` for security-focused plans. |
| `validation` | Optional list of shell commands; run with `validate` subcommand or `--validate-after` after `--force-execute` |

## Bundled examples

| File | Purpose |
|------|---------|
| `template.task.json` | Empty fields to copy |
| `example-feature.task.json` | Generic feature-style task |
| `example-bugfix.task.json` | Bugfix-oriented task |
| `secure-refactor-analysis.task.json` | **Analyze repo and propose a secure refactor plan** (read-only planning) |

## Sample: secure refactor analysis

```bash
./scripts/sample-secure-refactor-plan.sh
```

Or:

```bash
python3 -m agent plan --task tasks/secure-refactor-analysis.task.json
```

See also `examples/flows/secure-refactor-sample.md`.
