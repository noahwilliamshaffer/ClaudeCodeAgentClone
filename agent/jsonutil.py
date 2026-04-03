"""Extract JSON objects from model outputs (markdown fences or raw)."""

from __future__ import annotations

import json
import re
from typing import Any


def extract_json_object(text: str) -> dict[str, Any]:
    """Return the first JSON object found in text."""
    text = text.strip()
    # ```json ... ```
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if fence:
        inner = fence.group(1).strip()
        return json.loads(inner)
    # Raw object
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("No JSON object found in model output")


def extract_json_array(text: str) -> list[Any]:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if fence:
        inner = fence.group(1).strip()
        return json.loads(inner)
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("No JSON array found in model output")
