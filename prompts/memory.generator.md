# Repo summary generator

Given a **list of file paths** (not full file contents), infer the repository structure.

Return JSON in a single markdown fenced block using exactly this shape:

```json
{
  "purpose": "One sentence describing what the repository is for.",
  "layout": [
    { "name": "agent/", "description": "Python orchestration package" },
    "scripts/ — shell entrypoints for Cursor terminal"
  ],
  "conventions": [
    "Bullet points inferred from file names and directories",
    "Use read-only analysis when the snapshot is thin"
  ],
  "tech_stack": [
    "python",
    "bash"
  ],
  "agent_notes": "Short guidance for future agents working in this repository."
}
```

If the repository is ambiguous from paths alone, state assumptions explicitly in `agent_notes`.
