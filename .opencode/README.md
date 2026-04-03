# OpenCode bridge (`.opencode/`)

OpenCode discovers configuration from:

- Project `opencode.json` (workspace root)
- Optional `.opencode/{agents,commands,modes,plugins,skills,tools}/` per [OpenCode docs](https://open-code.ai/docs/en/config)

This repository keeps **canonical** skills under `/skills` and references them from `opencode.json` via the `instructions` array.

## Optional: duplicate skills here

If you want OpenCode-specific skill packaging without changing `instructions`, copy or symlink:

```bash
ln -s ../skills/*.md .opencode/skills/
```

(On Windows, copy files instead.)

## Agents

Add markdown agents under `.opencode/agents/` when you want named `opencode run --agent <name>` workflows.
