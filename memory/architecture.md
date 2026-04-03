# Architecture notes (edit me)

## Components

- `agent/` — Python orchestrator (planner / executor / reviewer / memory).
- `prompts/` — prompt templates consumed by the orchestrator and optionally by OpenCode.
- `skills/` — reusable behavior modules (markdown).
- `config/` — model names, workspace paths, guardrails.
- `scripts/` — thin bash wrappers for Cursor terminal workflows.

## Data flow

1. Task JSON → Planner (Ollama) → plan JSON + markdown.
2. Plan step → Executor (Ollama) → proposed actions → (dry-run or apply).
3. Optional validation commands from task JSON.
4. Reviewer (Ollama) reads git diff stats + task.

## Extension points

- Swap models in `config/models.json`.
- Add skills in `skills/` and reference them from tasks.
- Adjust `opencode.json` for interactive OpenCode sessions.
