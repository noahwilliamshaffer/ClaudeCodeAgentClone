# Skills

Skills are **markdown instructions** loaded by the Python orchestrator and referenced by task JSON (`"skill": "feature-implementation"`).

OpenCode also reads instructions via `opencode.json` → `instructions` (see project root).

## Add a skill

1. Create `skills/<id>.md` describing behavior, constraints, and output format.
2. Use the id in a task file: `"skill": "<id>"`.
3. Keep skills **focused**; compose with prompts in `/prompts` rather than duplicating long system text.

## Bundled skills

| Skill | Purpose |
|-------|---------|
| `codebase-analysis` | Map structure, dependencies, risks (read-heavy) |
| `feature-implementation` | Implement features incrementally |
| `bug-fixing` | Reproduce → isolate → fix → verify |
| `refactor-review` | Safe refactors with behavior preservation |
| `test-generation` | Add/adjust tests with minimal churn |
| `documentation-writer` | Clear docs aligned with repo tone |
| `security-review` | Threat model + unsafe patterns |
| `command-safety` | Shell hygiene, quoting, destructive-op avoidance |
| `repo-onboarding` | Fast orientation for new contributors |
