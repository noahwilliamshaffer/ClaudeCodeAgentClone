"""Minimal Ollama HTTP client (stdlib only)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class OllamaError(Exception):
    message: str
    status: int | None = None

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message


def chat(
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,
    num_ctx: int | None = None,
    stream: bool = False,
) -> str:
    """Call /api/chat and return the assistant message content."""
    url = base_url.rstrip("/") + "/api/chat"
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "options": {"temperature": temperature},
    }
    if num_ctx is not None:
        body["options"]["num_ctx"] = num_ctx

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise OllamaError(e.read().decode("utf-8", errors="replace"), e.code) from e
    except urllib.error.URLError as e:
        raise OllamaError(str(e.reason)) from e

    payload = json.loads(raw)
    msg = payload.get("message") or {}
    content = msg.get("content")
    if not content:
        raise OllamaError("Empty response from Ollama")
    return content


def list_models(base_url: str) -> list[str]:
    url = base_url.rstrip("/") + "/api/tags"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    models = []
    for m in data.get("models", []):
        name = m.get("name")
        if name:
            models.append(name)
    return models
