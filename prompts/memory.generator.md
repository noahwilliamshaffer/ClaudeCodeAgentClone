# Repo summary generator

Given a **list of file paths** (not full file contents), infer the repository structure.

Return JSON in a ```json fence:

```json
{
  "purpose": "one sentence",
  "layout": [
    { "name": "agent/", "description": "orchestration code" },
    "skills/ — reusable behaviors"
  ],
  "conventions": ["bullet points about style or architecture if inferable from paths"],
  "tech_stack": ["python", "bash", ...],
  "agent_notes": "short guidance for future agents working in this repo"
}
```

If the repo is ambiguous, state assumptions explicitly in `agent_notes`.
