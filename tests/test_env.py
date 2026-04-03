"""Tests for agent.env resolve_ollama_base_url."""

from __future__ import annotations

import os

from agent.config_loader import ModelsConfig
from agent.env import resolve_ollama_base_url


def test_env_overrides_config(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "http://example:11434")
    m = ModelsConfig(
        ollama_base_url="http://127.0.0.1:11434",
        models={"planner": "x"},
        options={},
        ollama_host_env="OLLAMA_HOST",
    )
    assert resolve_ollama_base_url(m) == "http://example:11434"


def test_config_when_env_unset(monkeypatch):
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    m = ModelsConfig(
        ollama_base_url="http://127.0.0.1:11434",
        models={"planner": "x"},
        options={},
    )
    assert resolve_ollama_base_url(m) == "http://127.0.0.1:11434"
