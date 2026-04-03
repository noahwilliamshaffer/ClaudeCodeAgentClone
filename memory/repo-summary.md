# Repository summary

This repository provides a **local-first agent workspace**: Python orchestration (`agent/`) for planning, execution, review, and memory using **Ollama** by default, with an optional **OpenCode** transport layer. Shell scripts under `scripts/` target a **Cursor**-centric workflow.

## Layout

| Path | Role |
|------|------|
| `agent/` | CLI and flows (`plan`, `execute`, `review`, `memory`, `loop`, `doctor`, `validate`) |
| `config/` | Model names, Ollama URL, workspace paths, guardrails |
| `prompts/` | Planner, executor, reviewer, and memory prompt templates |
| `skills/` | Markdown skill modules referenced by task JSON |
| `tasks/` | Task definitions (`*.task.json`) |
| `memory/` | Conventions, architecture notes, generated plans |
| `docs/` | Integration documentation (OpenCode) |
| `tests/` | Pytest suite for core utilities |

## Tech stack

- Python 3.11+ (stdlib orchestration; no required pip deps for runtime)
- Ollama HTTP API (`config/models.json`, optional `OLLAMA_HOST`)
- Optional: OpenCode CLI when `OPENCODE_RUNTIME=1`

## Conventions

See `memory/conventions.md`. Execution defaults to **dry-run**; use `--force-execute` only after reviewing proposed actions.

---

*To refresh this file from a model, run `./scripts/memory-update.sh`.*
