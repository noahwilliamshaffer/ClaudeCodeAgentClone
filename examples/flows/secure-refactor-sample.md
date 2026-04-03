# Sample: analyze repository and propose a secure refactor plan

This example uses the **secure refactor** task, which selects `prompts/planner.secure-refactor.md` and the `secure-refactor-planning` skill.

## One command (planning only)

```bash
./scripts/sample-secure-refactor-plan.sh
```

Equivalent manual steps:

```bash
python3 -m agent doctor
python3 -m agent plan --task tasks/secure-refactor-analysis.task.json
```

## Prerequisites

- `ollama serve` running locally
- Models from `config/models.json` pulled, for example:

```bash
ollama pull llama3.2:latest
ollama pull qwen2.5-coder:latest
```

## Outputs

- `memory/plans/secure-refactor-analysis-001.plan.json` — structured plan including `security_findings` and `refactor_recommendations` when the model follows the schema
- `memory/plans/secure-refactor-analysis-001.plan.md` — readable summary with optional security sections

## Validation commands on the task

The task includes `python3 -m compileall -q agent` and `python3 -m pytest -q tests/`. These run when you use executor/loop with `--validate-after` after `--force-execute`; for **plan-only** analysis they are not required.

## Natural-language prompt (OpenCode optional)

If you use OpenCode interactively in this directory, you can ask the same intent in prose; the JSON task file keeps the Python orchestrator deterministic:

```bash
./scripts/opencode-run.sh "Read prompts/planner.secure-refactor.md and skills/secure-refactor-planning.md, then analyze this repo and list security findings and refactor recommendations."
```
