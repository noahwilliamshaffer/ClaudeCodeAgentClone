# Repository summary (template)

You can either:

1. Run `./scripts/memory-update.sh` (or `python3 -m agent memory`) to generate `memory/repo-summary.md` using the configured Ollama model, or  
2. Fill in this template by hand and save as `memory/repo-summary.md`.

## Purpose

Describe what this repository is for in one short paragraph.

## Layout

- `agent/` — Python package: planner, executor, reviewer, memory flows
- `config/` — `models.json`, `workspace.json`, `guardrails.json`
- `scripts/` — Bash wrappers for common commands
- `tasks/` — JSON task definitions consumed by the CLI

## Conventions

Link to `memory/conventions.md` for team-specific rules. For this scaffold, prefer small commits, stdlib-first Python, and dry-run before `--force-execute`.

## How to run

```bash
./scripts/bootstrap.sh
python3 -m agent doctor
./scripts/plan.sh --task tasks/secure-refactor-analysis.task.json
```

## Tech stack

- Python 3.11+
- Ollama (local LLM)
- Optional: OpenCode CLI

## Notes for agents

Keep guardrails enabled. Do not store API keys in tracked files; use environment variables or local untracked config.
