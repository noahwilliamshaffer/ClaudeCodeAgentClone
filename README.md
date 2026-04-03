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

## Agent pipeline (explicit loop)

The orchestrator implements a **stage graph** with **structured JSON state** persisted under `memory/runs/*.json`.

| Stage | Purpose |
|-------|---------|
| **intake** | Load and validate task JSON |
| **scan** | Repo file list + snapshot text for prompts |
| **plan** | LLM planner → `plan` + `plan_paths` |
| **select** | Choose active plan step index |
| **execute** | Executor for that step (dry-run unless `--execute`; always dry in `--safe`) |
| **validate** | Run `validation` commands from the task JSON |
| **review** | Reviewer pass |
| **memory** | Repo summary (`dry_run` when `--safe`) |
| **decide** | Next-step decision: `continue` / `complete` / `stop` |

**Full loop** (repeats execute→decide while decision is `continue`):

```bash
./scripts/pipeline.sh --task tasks/example-feature.task.json --safe
```

**Safe mode** (`--safe` or `AGENT_SAFE_MODE=1`): plans and reviews **without writing repo files** (executor dry-run, memory dry-run). Still runs LLM stages.

**Execute with real writes** (not safe):

```bash
./scripts/pipeline.sh --task tasks/example-feature.task.json --execute
```

**One stage at a time** (resume from saved state):

```bash
./scripts/pipeline.sh --task tasks/example-feature.task.json --state memory/runs/my-run.json --stage intake
./scripts/pipeline.sh --state memory/runs/my-run.json --stage scan
# … plan → select → execute → validate → review → memory → decide
```

Implementation: `agent/loop/stages.py`, `agent/loop/runner.py`, `agent/loop/state.py`, `prompts/decide.next.md`.

## Multi-Agent Architecture

This system uses a **single orchestrator** (`runner.py`) that delegates work to **5 specialized LLM roles**. Each role uses a potentially different model optimized for its task.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PIPELINE RUNNER (runner.py)                      │
│                    Orchestrates the entire workflow                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────┬───────────┬───┴───┬───────────┬───────────┐
        ▼           ▼           ▼       ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ PLANNER │ │EXECUTOR │ │REVIEWER │ │ MEMORY  │ │ DECIDE  │
   │         │ │         │ │         │ │         │ │         │
   │llama3.2 │ │qwen2.5- │ │qwen2.5- │ │llama3.2 │ │llama3.2 │
   │         │ │ coder   │ │ coder   │ │         │ │         │
   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

### The 5 Agent Roles

| Role | Default Model | Purpose | Input | Output |
|------|---------------|---------|-------|--------|
| **Planner** | `llama3.2` | Creates structured multi-step plans | Task + repo snapshot + skill template | JSON plan with phases, steps, risks |
| **Executor** | `qwen2.5-coder` | Generates code changes for one step | Plan step + repo context | File writes + shell commands |
| **Reviewer** | `qwen2.5-coder` | Reviews changes against requirements | Task + plan + git diff | Verdict: `approved` / `needs_follow_up` |
| **Memory** | `llama3.2` | Generates repo summaries | File list + conventions | Markdown summary for future context |
| **Decide** | `llama3.2` | Decides next action in the loop | Execution result + review | `continue` / `complete` / `stop` |

### How Task Delegation Works

**1. The Runner Controls Flow** (`agent/loop/runner.py`)

The orchestrator runs setup stages first, then loops through execution stages:

```python
# Setup stages (run once)
for name in ("intake", "scan", "plan"):
    run_one_stage(name, ctx, data, ...)

# Execution loop (repeats until complete/stop)
while rounds < max_rounds:
    for name in ("execute", "validate", "review", "memory", "decide"):
        run_one_stage(name, ctx, data, ...)
    
    if decision != "continue":
        break  # Exit loop
```

**2. Each Stage Calls One LLM Role**

Each flow module calls `complete_chat()` with a specific role name:

```python
# planner.py
content = complete_chat(root, models, "planner", messages)

# executor.py  
content = complete_chat(root, models, "executor", messages)

# reviewer.py
content = complete_chat(root, models, "reviewer", messages)

# decide.py
content = complete_chat(root, models, "decide", messages)
```

**3. Model Selection via Config** (`config/models.json`)

```json
{
  "models": {
    "planner": "llama3.2:latest",
    "executor": "qwen2.5-coder:latest",
    "reviewer": "qwen2.5-coder:latest",
    "memory": "llama3.2:latest",
    "decide": "llama3.2:latest"
  }
}
```

### Data Flow Between Agents

```
TASK JSON {id, title, description, skill, validation}
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│  1. PLANNER                                                   │
│  Input:  Task + Repo snapshot + Skill template               │
│  Output: Plan {summary, phases, steps[], risks}              │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  2. EXECUTOR (runs per step)                                  │
│  Input:  Plan step + Repo context                            │
│  Output: Actions [{write_file, path, content},               │
│                   {run_command, cmd}]                        │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  3. REVIEWER                                                  │
│  Input:  Task + Plan summary + Git diff                      │
│  Output: {verdict, regression_risks[], follow_up[]}          │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  4. DECIDE                                                    │
│  Input:  Execution result + Review verdict + Step index      │
│  Output: {decision: continue|complete|stop,                  │
│           next_step_index, rationale}                        │
└──────────────────────────┬───────────────────────────────────┘
                           │
               ┌───────────┴───────────┐
               ▼                       ▼
         [continue]               [complete/stop]
               │                       │
               ▼                       ▼
         Back to EXECUTOR          END LOOP
         (next step index)
```

### Key Design Patterns

| Pattern | Description |
|---------|-------------|
| **Specialized Models** | Code tasks use `qwen2.5-coder`; planning/reasoning uses `llama3.2` |
| **Structured JSON** | All agents output JSON in fenced blocks, parsed by `jsonutil.extract_json_object()` |
| **Heuristic Fallbacks** | If LLM fails, `decide.py` uses rule-based logic to determine next action |
| **Guardrails** | Executor checks all actions against safety rules before execution |
| **Persistent State** | `PipelineStateData` saved to JSON after each stage for resumable runs |

### Customizing Agent Behavior

- **Change models**: Edit `config/models.json` to swap models for any role
- **Modify prompts**: Edit files in `prompts/` (e.g., `planner.md`, `executor.md`, `reviewer.md`)
- **Add skills**: Create new `.md` files in `skills/` and reference them in task JSON
- **Adjust parameters**: Tune `temperature` and `num_ctx` per role in `config/models.json`

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
│   ├── loop/
│   │   ├── state.py
│   │   ├── stages.py
│   │   ├── runner.py
│   │   └── decide.py
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
