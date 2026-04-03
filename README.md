# Local agent workspace (OpenCode + Ollama + Cursor)

A **local-first** agentic coding workspace: **planning**, **controlled execution**, **review**, and **persistent memory**. The default runtime is **Ollama** over HTTP; **OpenCode** is optional and routed through a small adapter (`agent/llm.py`, `agent/opencode_adapter.py`). **No paid API is required.**

| Layer | Role |
|-------|------|
| **`agent/`** | Python orchestrator: CLI, flows, guardrails, JSON parsing, trace logging |
| **`opencode.json`** | OpenCode project defaults when using the OpenCode CLI interactively |
| **`prompts/` + `skills/`** | Prompt templates and reusable behaviors |
| **`config/`** | Models, Ollama URL, workspace paths, guardrails |
| **`scripts/`** | Bash entrypoints for Cursor’s terminal |
| **`docs/INTEGRATION-OPENCODE.md`** | OpenCode vs Ollama transport map |

## Prerequisites

- **Python 3.11+**
- **Ollama** — [ollama.com](https://ollama.com)
- **OpenCode** (optional) — [OpenCode CLI](https://open-code.ai/docs/en/cli)
- **Cursor** (recommended) — open this folder as the workspace root

## Quick start

```bash
chmod +x scripts/*.sh
./scripts/bootstrap.sh
```

Start Ollama, pull models, then:

```bash
python3 -m agent doctor
./scripts/plan.sh --task tasks/example-feature.task.json
```

## Sample: analyze this repo and propose a secure refactor plan

This runs the **planner only** (no executor writes). It uses `prompts/planner.secure-refactor.md` and `skills/secure-refactor-planning.md`.

```bash
./scripts/sample-secure-refactor-plan.sh
```

Manual equivalent:

```bash
python3 -m agent doctor
python3 -m agent plan --task tasks/secure-refactor-analysis.task.json
```

Open outputs:

- `memory/plans/secure-refactor-analysis-001.plan.md`
- `memory/plans/secure-refactor-analysis-001.plan.json`

More detail: `examples/flows/secure-refactor-sample.md`.

## Installing Ollama

```bash
ollama --version
ollama pull llama3.2:latest
ollama pull qwen2.5-coder:latest
```

Match tags in **`config/models.json`**. Optional: set **`OLLAMA_HOST`** (see `config/models.json` and `.env.example`).

## Ollama immediately (default)

- Orchestrator calls **`http://127.0.0.1:11434`** (or `OLLAMA_HOST`) via `agent/ollama_client.py`.
- **`OPENCODE_RUNTIME`** unset → all LLM calls use Ollama directly.

```bash
python3 -m agent doctor
```

## Optional: OpenCode as LLM transport

Set:

```bash
export OPENCODE_RUNTIME=1
```

Then `agent/llm.py` uses `opencode run` (see `docs/INTEGRATION-OPENCODE.md`). Interactive use:

```bash
./scripts/opencode-run.sh "Summarize the repository layout."
```

## Execute / review / loop

Dry-run executor (default):

```bash
./scripts/execute.sh --task tasks/example-feature.task.json \
  --plan memory/plans/example-feature-001.plan.json --step 0
```

Apply writes and commands:

```bash
./scripts/execute.sh --task tasks/example-feature.task.json \
  --plan memory/plans/example-feature-001.plan.json --step 0 \
  --force-execute --validate-after
```

Review:

```bash
./scripts/review.sh --task tasks/example-feature.task.json \
  --plan memory/plans/example-feature-001.plan.json
```

Full loop:

```bash
./scripts/loop.sh --task tasks/example-feature.task.json
```

## Safe mode vs execute mode

| Mode | Behavior |
|------|----------|
| **Dry-run** | Executor reports `write_file` / `run_command` without applying |
| **Execute** | Pass **`--force-execute`** to apply changes |

Guardrails: **`config/guardrails.json`** (blocked paths, command substrings, size limits).

## Tests

```bash
pip install -r requirements-dev.txt
PYTHONPATH=. python3 -m pytest tests/ -q
```

`./scripts/bootstrap.sh` runs tests when `pytest` is installed.

## Task format

See **`tasks/README.md`**. Key optional field: **`planner_prompt`** for alternate planner templates.

## Memory

- **`memory/conventions.md`**, **`memory/architecture.md`** — hand-edited
- **`memory/repo-summary.md`** — starter file; regenerate with `./scripts/memory-update.sh`

## Logs

- **`logs/agent-trace.log`** — append-only JSONL trace (path in `config/workspace.json` → `trace_log`)

## Environment variables

| Variable | Purpose |
|----------|---------|
| `OLLAMA_HOST` | Overrides `ollama_base_url` from `config/models.json` |
| `OPENCODE_RUNTIME` | Set to `1` / `true` / `yes` to route LLM calls through OpenCode CLI |
| `OPENCODE_CONFIG` | Optional path to OpenCode JSON config (OpenCode standard) |

Copy **`.env.example`** to `.env` for local overrides (do not commit secrets).

## Repository layout

```
.
├── .cursor/rules/
├── .env.example
├── agent/
│   ├── cli.py
│   ├── config_loader.py
│   ├── env.py
│   ├── guardrails.py
│   ├── jsonutil.py
│   ├── llm.py
│   ├── ollama_client.py
│   ├── opencode_adapter.py
│   ├── repo_context.py
│   ├── skills.py
│   ├── trace.py
│   └── flows/
├── config/
├── docs/
│   └── INTEGRATION-OPENCODE.md
├── examples/flows/
├── memory/
├── prompts/
├── scripts/
├── skills/
├── tasks/
├── tests/
├── opencode.json
├── pyproject.toml
├── requirements-dev.txt
├── requirements.txt
└── README.md
```

## Troubleshooting

- **`doctor` fails**: start `ollama serve`; check `OLLAMA_HOST` and firewall.
- **Bad JSON from models**: `agent/jsonutil.py` tolerates fences and prose; lower temperature in `config/models.json` if needed.
- **SSH to GitHub**: use port 443 if 22 is blocked (`ssh.github.com`).

## Publishing changes to GitHub

Upstream: [noahwilliamshaffer/ClaudeCodeAgentClone](https://github.com/noahwilliamshaffer/ClaudeCodeAgentClone) (`main`).

```bash
git add -A
git commit -m "Describe the change clearly"
git push origin main
```

See `.cursor/rules/git-github.mdc`.

## Future upgrades

- Unified-diff patches in the executor (smaller edits than full-file writes)
- Optional SQLite memory for cross-session retrieval
- MCP tools via OpenCode when you need external systems

---

This scaffold keeps **Ollama** as the default path, **OpenCode** behind an adapter, and everything runnable from **Cursor** with a small set of scripts.
