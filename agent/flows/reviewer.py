"""Reviewer flow — checks diffs and task satisfaction."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from ..config_loader import AgentPaths, ModelsConfig
from ..jsonutil import extract_json_object
from ..llm import complete_chat
from ..trace import append_trace


def _git_diff(root: Path) -> str:
    if not (root / ".git").is_dir():
        return "(no git repository — empty diff)"
    try:
        p = subprocess.run(
            ["git", "-C", str(root), "diff", "--stat", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        return (p.stdout or "") + (p.stderr or "")
    except FileNotFoundError:
        return "(git not installed)"


def run_reviewer(
    root: Path,
    paths: AgentPaths,
    models: ModelsConfig,
    task: dict[str, Any],
    plan: dict[str, Any] | None,
    *,
    trace_path: Path,
) -> dict[str, Any]:
    template = (paths.prompts_dir / "reviewer.md").read_text(encoding="utf-8")
    diff = _git_diff(root)
    user = f"""
{template}

## Task
{json.dumps(task, indent=2)}

## Plan summary
{json.dumps(plan.get("summary") if plan else None, indent=2)}

## Diff / change stats
{diff}

Follow the output format (JSON in a fenced block) defined in the reviewer template above.
"""
    messages = [
        {"role": "system", "content": "You are a senior reviewer. Output JSON only in a ```json fence."},
        {"role": "user", "content": user},
    ]
    content = complete_chat(root, models, "reviewer", messages)
    parsed = extract_json_object(content)
    append_trace(trace_path, "review", {"verdict": parsed.get("verdict")})
    out_path = paths.logs_dir / "last-review.json"
    out_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
    return {"review": parsed, "path": str(out_path)}
