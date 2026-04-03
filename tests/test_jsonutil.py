"""Tests for agent.jsonutil."""

from __future__ import annotations

import pytest

from agent.jsonutil import extract_json_object


def test_fence_json():
    text = """Here is the result:
```json
{"a": 1, "b": "two"}
```
"""
    assert extract_json_object(text) == {"a": 1, "b": "two"}


def test_prose_before_json():
    text = """Thoughts: we should proceed.

Here's the object:
{
  "summary": "hello",
  "steps": []
}
Thanks."""
    out = extract_json_object(text)
    assert out["summary"] == "hello"
    assert out["steps"] == []


def test_nested_braces_in_string():
    text = r"""
```json
{"msg": "use {curlies} in strings", "n": 2}
```
"""
    assert extract_json_object(text)["msg"] == "use {curlies} in strings"


def test_prose_raw_decode_braces_in_string():
    text = 'Prefix text {"msg": "brace { inside } string", "ok": true} suffix'
    out = extract_json_object(text)
    assert out["msg"] == "brace { inside } string"
    assert out["ok"] is True


def test_no_json_raises():
    with pytest.raises(ValueError):
        extract_json_object("no json here")


def test_first_fence_wins():
    text = """
```json
{"first": true}
```
```json
{"second": true}
```
"""
    assert extract_json_object(text) == {"first": True}
