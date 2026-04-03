"""Extract JSON objects from model outputs (markdown fences, prose, or raw)."""

from __future__ import annotations

import json
import re
from typing import Any


def _try_load_object(s: str) -> dict[str, Any] | None:
    try:
        v = json.loads(s)
        return v if isinstance(v, dict) else None
    except json.JSONDecodeError:
        return None


def extract_json_object(text: str) -> dict[str, Any]:
    """
    Return the first JSON object found in ``text``.

    Strategy:
    1. Every markdown fenced block (``` or ```json); parse inner text.
    2. Scan for ``{`` and use ``JSONDecoder.raw_decode`` so strings containing ``{`` or ``}``
       do not break parsing.
    """
    raw = text.strip()
    if not raw:
        raise ValueError("Empty model output")

    for m in re.finditer(r"```(?:json|JSON)?\s*([\s\S]*?)```", raw):
        inner = m.group(1).strip()
        parsed = _try_load_object(inner)
        if parsed is not None:
            return parsed

    decoder = json.JSONDecoder()
    for m in re.finditer(r"\{", raw):
        try:
            obj, _end = decoder.raw_decode(raw, m.start())
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue

    raise ValueError("No JSON object found in model output")


def extract_json_array(text: str) -> list[Any]:
    """Return the first JSON array found in ``text``."""
    raw = text.strip()
    if not raw:
        raise ValueError("Empty model output")

    for m in re.finditer(r"```(?:json|JSON)?\s*([\s\S]*?)```", raw):
        inner = m.group(1).strip()
        try:
            v = json.loads(inner)
            if isinstance(v, list):
                return v
        except json.JSONDecodeError:
            continue

    decoder = json.JSONDecoder()
    for m in re.finditer(r"\[", raw):
        try:
            obj, _end = decoder.raw_decode(raw, m.start())
            if isinstance(obj, list):
                return obj
        except json.JSONDecodeError:
            continue

    raise ValueError("No JSON array found in model output")
