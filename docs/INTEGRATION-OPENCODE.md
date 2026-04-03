# OpenCode integration map

This workspace runs **standalone** on **Ollama** (HTTP). **OpenCode** is **optional** and wired through a narrow adapter so you can change transports without rewriting planner/executor/reviewer logic.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  agent/flows/*.py  (planner, executor, reviewer, memory)   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  agent/llm.py  →  complete_chat(workspace_root, models, ...) │
└───────────────┬─────────────────────────┬──────────────────┘
                │                         │
     OPENCODE_RUNTIME unset/false         OPENCODE_RUNTIME=1
                │                         │
                ▼                         ▼
┌───────────────────────┐     ┌──────────────────────────────┐
│ agent/ollama_client.py │     │ agent/opencode_adapter.py     │
│ POST /api/chat         │     │ subprocess: opencode run ...  │
└───────────┬────────────┘     └───────────────┬──────────────┘
            │                                   │
            ▼                                   ▼
     Ollama daemon                       OpenCode CLI → provider
     (127.0.0.1:11434)                  (may use Ollama backend per opencode.json)
```

## Default path (Ollama only)

1. Install and run [Ollama](https://ollama.com).
2. Pull models listed in `config/models.json`.
3. Run `./scripts/bootstrap.sh` and `python3 -m agent doctor`.

No OpenCode installation required.

## Optional path (OpenCode as transport)

1. Install [OpenCode CLI](https://open-code.ai/docs/en/cli) and ensure `opencode` is on `PATH`.
2. Keep project `opencode.json` aligned with local models (`ollama/<tag>`).
3. Export **`OPENCODE_RUNTIME=1`** in your shell (or add to `.env` and load it before running).

```bash
export OPENCODE_RUNTIME=1
python3 -m agent plan --task tasks/secure-refactor-analysis.task.json
```

Behavior:

- `agent/llm.py` flattens chat `messages` into one prompt string (`messages_to_prompt`).
- `opencode_adapter.complete_with_opencode` runs `opencode run -m ollama/<model> "<prompt>"` from the **workspace root** so `opencode.json` and `instructions` apply.

**Limitations (by design):**

- This does **not** expose OpenCode’s full tool loop inside Python; it only substitutes **text generation**.
- Per-request temperature may follow `opencode.json` / provider defaults, not Python `options` alone.
- For interactive sessions, TUI, or MCP tools, use `opencode` directly or `opencode serve` (see upstream docs).

## Configuration files

| File | Role |
|------|------|
| `opencode.json` | Project OpenCode defaults (model, instructions, permissions). |
| `config/models.json` | Python orchestrator models and Ollama URL; `OLLAMA_HOST` overrides base URL. |
| `OPENCODE_CONFIG` | Optional env var (OpenCode standard) to point at an alternate JSON config path. |

## Integration points for future work

| Goal | Suggested extension |
|------|----------------------|
| HTTP OpenCode server | Add `agent/opencode_server_client.py` calling `opencode serve` REST API; swap in `llm.py`. |
| File attachments | Pass `attached_files` from tasks into `opencode_run` (adapter already supports `--file`). |
| Session continuity | Use `opencode run --continue` / `--session` (extend `opencode_adapter`). |

## References

- [OpenCode CLI](https://open-code.ai/docs/en/cli)
- [OpenCode configuration](https://open-code.ai/docs/en/config)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)
