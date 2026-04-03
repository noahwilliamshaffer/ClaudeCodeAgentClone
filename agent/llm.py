"""
Unified chat completion: **Ollama HTTP API** (default) or **OpenCode CLI** (optional).

Integration boundary
--------------------
- **Ollama**: always used when ``OPENCODE_RUNTIME`` is unset/false. This is the default,
  local-first path (no OpenCode dependency).
- **OpenCode**: when ``OPENCODE_RUNTIME=1`` (or ``true``/``yes``) *and* ``opencode`` is on
  ``PATH``, requests are sent through ``opencode run`` (see ``opencode_adapter``).

OpenCode’s internal tool loop and provider matrix may differ from this orchestrator; this
module only substitutes the **text generation** step so prompts stay identical. For full
OpenCode agent features (tools, sessions), run ``opencode`` interactively or use
``opencode serve`` and attach — documented in ``docs/INTEGRATION-OPENCODE.md``.
"""

from __future__ import annotations

from pathlib import Path

from .config_loader import ModelsConfig
from . import opencode_adapter
from .env import resolve_ollama_base_url
from .ollama_client import chat as ollama_chat


def messages_to_prompt(messages: list[dict[str, str]]) -> str:
    """Flatten chat messages into a single prompt string for OpenCode CLI."""
    blocks: list[str] = []
    for m in messages:
        role = m.get("role", "user").strip().upper()
        content = m.get("content", "").strip()
        blocks.append(f"[{role}]\n{content}")
    return "\n\n---\n\n".join(blocks)


def complete_chat(
    workspace_root: Path,
    models: ModelsConfig,
    role: str,
    messages: list[dict[str, str]],
) -> str:
    """
    Run one chat completion for the given role key (planner, executor, reviewer, memory).

    Uses OpenCode only when ``should_use_opencode()`` is true and the binary exists;
    otherwise calls Ollama directly.
    """
    model = models.models[role]
    opt = models.options.get(role, {})
    temperature = float(opt.get("temperature", 0.2))
    num_ctx = int(opt["num_ctx"]) if opt.get("num_ctx") is not None else None

    if opencode_adapter.should_use_opencode() and opencode_adapter.opencode_available():
        prompt = messages_to_prompt(messages)
        return opencode_adapter.complete_with_opencode(
            workspace_root,
            prompt,
            model=model,
            temperature=temperature,
        )

    base = resolve_ollama_base_url(models)
    return ollama_chat(
        base,
        model,
        messages,
        temperature=temperature,
        num_ctx=num_ctx,
    )


def list_local_models(models: ModelsConfig) -> list[str]:
    """List Ollama model tags (for doctor)."""
    from .ollama_client import list_models

    base = resolve_ollama_base_url(models)
    return list_models(base)
