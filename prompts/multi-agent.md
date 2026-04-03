# Multi-agent coordination (optional pattern)

This workspace supports a **sequential multi-agent** pattern without paid APIs:

1. **Planner agent** — produces structured JSON + markdown plan (`python3 -m agent plan`).
2. **Executor agent** — applies one step at a time with dry-run default (`python3 -m agent execute`).
3. **Reviewer agent** — checks diffs and requirements (`python3 -m agent review`).
4. **Memory agent** — refreshes `memory/repo-summary.md` (`python3 -m agent memory`).

## OpenCode integration

- Interactive: run `opencode` in this directory to use the same `opencode.json` model defaults.
- Scriptable: `opencode run -m ollama/<model> "prompt"` with `--file` attachments for plans/tasks.

## Future: parallel agents

- Run two terminals with different `config/models.json` entries (e.g. planner vs executor model).
- Merge outputs manually or with a small merge script — keep human review in the loop.
