"""Environment and configuration helpers for runtime (Ollama URL, feature flags)."""

from __future__ import annotations

import os

from .config_loader import ModelsConfig


def resolve_ollama_base_url(models: ModelsConfig) -> str:
    """
    Effective Ollama API base URL.

    Precedence:
    1. Environment variable named in models.json `ollama_host_env` (default `OLLAMA_HOST`)
    2. `ollama_base_url` from models.json
    """
    key = getattr(models, "ollama_host_env", "OLLAMA_HOST") or "OLLAMA_HOST"
    env_val = os.environ.get(key, "").strip()
    if env_val:
        return env_val.rstrip("/")
    return models.ollama_base_url.rstrip("/")
