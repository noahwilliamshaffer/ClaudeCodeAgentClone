# Memory

Persistent, **local** context for agents:

- `conventions.md` — team conventions and style (edit by hand).
- `architecture.md` — high-level design notes (edit by hand).
- `repo-summary.md` — generated summary (`python3 -m agent memory` or `./scripts/memory-update.sh`).
- `plans/` — planner outputs (`*.plan.json`, `*.plan.md`).
- `runs/` — pipeline state JSON (`python3 -m agent pipeline …`).

Nothing here should contain secrets. Keep secrets out of the repo.
