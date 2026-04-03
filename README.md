# Local agent workspace (OpenCode + Ollama + Cursor)

A **local-first**, **production-style** scaffold for agentic coding: planning, controlled execution, review, and persistent memory — with **no paid API required**.

| Layer | Role |
|-------|------|
| **Python `agent/` package** | Orchestrator: planner / executor / reviewer / memory (uses **Ollama HTTP API**). |
| **`opencode.json`** | OpenCode project defaults (models, instructions, permissions). |
| **`skills/` + `prompts/`** | Reusable behaviors and prompt templates. |
| **`config/`** | Model names, workspace paths, guardrails (single place to swap models). |
| **`scripts/`** | Thin bash wrappers optimized for **Cursor’s integrated terminal**. |

## Prerequisites

- **Python 3.11+** (`python3` on PATH)
- **Ollama** — local model runtime ([ollama.com](https://ollama.com))
- **OpenCode** (optional for interactive TUI / `opencode run`) — [OpenCode docs](https://open-code.ai/docs/en/cli)
- **Cursor** (recommended IDE) — open this folder as the workspace root

## Quick start (Cursor workflow)

1. **Open this repository in Cursor** (`File → Open Folder`).
2. Open the **integrated terminal** at the repo root.
3. Run:

```bash
chmod +x scripts/*.sh   # first clone only
./scripts/bootstrap.sh
```

4. Start **Ollama** (if not already running) and pull models (see below).
5. **Plan** from a task file:

```bash
./scripts/plan.sh --task tasks/example-feature.task.json
```

6. Inspect `memory/plans/*.plan.md` and the matching `.plan.json`.
7. **Execute** a single step in **safe (dry-run) mode** (default):

```bash
./scripts/execute.sh \
  --task tasks/example-feature.task.json \
  --plan memory/plans/example-feature-001.plan.json \
  --step 0
```

8. When you accept the proposed actions, re-run with **`--force-execute`** to apply writes and run commands:

```bash
./scripts/execute.sh \
  --task tasks/example-feature.task.json \
  --plan memory/plans/example-feature-001.plan.json \
  --step 0 \
  --force-execute \
  --validate-after
```

9. **Review**:

```bash
./scripts/review.sh --task tasks/example-feature.task.json --plan memory/plans/example-feature-001.plan.json
```

10. **Health check** (Ollama reachable):

```bash
python3 -m agent doctor
```

### One-shot loop (plan → all steps → review)

Dry-run (default):

```bash
./scripts/loop.sh --task tasks/example-feature.task.json
```

Apply changes + run task validations:

```bash
./scripts/loop.sh --task tasks/example-feature.task.json --force-execute --validate-after
```

## Installing Ollama

Follow the official install for your OS: [https://ollama.com/download](https://ollama.com/download)

Verify:

```bash
ollama --version
ollama serve   # if you need the daemon explicitly
```

## Recommended models (two profiles)

Edit **`config/models.json`** to match tags you actually pulled.

| Role | Suggested Ollama model | Notes |
|------|------------------------|-------|
| **Planner** (fast / structured) | `llama3.2:latest` | Lightweight planning / summaries |
| **Executor** (coding) | `qwen2.5-coder:latest` | Strong general coding assistance |

Pull examples:

```bash
ollama pull llama3.2:latest
ollama pull qwen2.5-coder:latest
```

Keep **`opencode.json`** `model` / `small_model` in sync with how you want OpenCode interactive sessions to behave (format `ollama/<tag>`).

## Installing or verifying OpenCode

See the official CLI docs: [OpenCode CLI](https://open-code.ai/docs/en/cli)

Common install paths add `opencode` to PATH. Verify:

```bash
opencode --version
```

### How OpenCode consumes this repo

- **Project config**: `opencode.json` at the repo root sets defaults and `instructions` (skills + prompts).
- **Non-interactive prompt**:

```bash
./scripts/opencode-run.sh "Summarize the agent architecture in 10 bullets"
```

- **Python isolation**: orchestration lives in `agent/`; OpenCode is optional for interactive work and `opencode run` automation. The adapter is `agent/opencode_adapter.py`.

## Safe mode vs execute mode

| Mode | Behavior |
|------|----------|
| **Safe / dry-run** (default) | Executor **prints** proposed `write_file` and `run_command` actions without applying them. |
| **Execute** | Pass **`--force-execute`** to `execute` or `loop` to write files and run commands. |

Guardrails live in **`config/guardrails.json`** (blocked paths, size limits, command substring blocks). Writes to `.env`-like paths are rejected by default.

## Task format

See `tasks/template.task.json` and `tasks/example-feature.task.json`.

- **`skill`**: filename in `skills/` without `.md`.
- **`validation`**: list of shell commands run when you pass `--validate-after` (after `--force-execute`).

## Memory / context

- Hand-edited: `memory/conventions.md`, `memory/architecture.md`
- Generated: `memory/repo-summary.md` via `./scripts/memory-update.sh` or `python3 -m agent memory`
- Planner outputs: `memory/plans/`

## Adding a new skill

1. Create `skills/<id>.md` with behavior and constraints.
2. Reference `"skill": "<id>"` in your task JSON.
3. Optionally add the file to `opencode.json` → `instructions` (already includes `skills/**/*.md`).

## Changing models (single config file)

Edit **`config/models.json`**:

- `models.planner`, `models.executor`, `models.reviewer`, `models.memory`
- `options.*` for `temperature` and `num_ctx`

For OpenCode interactive defaults, mirror changes in **`opencode.json`** (`model`, `small_model`).

## Logs and trace

- Append-only JSONL trace: `logs/agent-trace.log` (see `config/workspace.json` → `trace_log`)
- File backups (when executing writes): `logs/backups/`

## Multi-agent style workflows (optional)

This repo implements **sequential** roles (planner → executor → reviewer). For parallel agents later:

- Run **separate terminals** with different `config/models.json` entries.
- Point each at the same repo; merge outputs in `memory/plans/` and PRs manually or with a small merge script.
- OpenCode supports multiple agents via `.opencode/agents/` and `opencode run --agent` ([docs](https://open-code.ai/docs/en/config)).

## Repository layout

```
.
├── .cursor/rules/         # Cursor guidance (e.g. GitHub publish workflow)
├── agent/                 # Python orchestrator
├── config/                # models.json, workspace.json, guardrails.json
├── prompts/               # planner / executor / reviewer / memory prompts
├── skills/                # reusable skill markdown
├── memory/                # persistent notes + generated summary + plans
├── tasks/                 # task JSON definitions
├── scripts/               # bootstrap, plan, execute, review, loop, memory-update
├── examples/flows/        # illustrative outputs
├── logs/                  # trace + backups (gitignored appropriately)
├── opencode.json          # OpenCode project config
└── README.md
```

## Troubleshooting

- **`python3 -m agent doctor` fails**: start Ollama (`ollama serve`) and confirm `config/models.json` → `ollama_base_url`.
- **Empty or bad JSON from models**: re-run with a stronger model or lower temperature in `config/models.json`.
- **Git operations**: initialize a repo (`git init`) so `git ls-files` snapshots and reviewer diffs work better.

## Publishing changes to GitHub

Upstream repository: [noahwilliamshaffer/ClaudeCodeAgentClone](https://github.com/noahwilliamshaffer/ClaudeCodeAgentClone) (`main`).

After you change the project, **commit with a clear message** and **push** so the remote stays current:

```bash
git status
git add -A
git commit -m "Short imperative summary of what changed

Optional body: why, scope, or follow-ups."
git push origin main
```

**Good commit messages** name the area and the change (examples: `Document Ollama model swap in config`, `Fix executor dry-run skipping validation`). **Avoid** empty or generic one-word messages unless you immediately amend with detail.

Cursor / agent helpers in this repo follow `.cursor/rules/git-github.mdc` so automated edits aim to end with the same publish step when appropriate.

## Future upgrades

- Add **pytest** + golden tests for `jsonutil` and guardrails.
- Wire **MCP tools** (OpenCode `opencode mcp`) for browser/docs without leaving the IDE.
- Optional **Redis/SQLite** memory for cross-session retrieval.
- **Structured patch** format (unified diff) instead of full-file writes for smaller deltas.
- **Parallel workers** with a merge queue and explicit file ownership locks.

---

This scaffold is intentionally **modular**: swap **Ollama** models in one JSON file, keep **OpenCode** as an optional shell, and iterate from **Cursor** with a small set of scripts.
