"""Reviewer flow — checks diffs and task satisfaction."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from ..config_loader import AgentPaths, ModelsConfig
from ..jsonutil import extract_json_object
from ..ollama_client import chat
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

Respond with JSON in a ```json fence:
{{
  "verdict": "pass" | "needs_follow_up",
  "regression_risks": ["..."],
  "requirements_coverage": "short assessment",
  "follow_up": [{{ "title": "", "rationale": "" }}]
}}
"""
    messages = [
        {"role": "system", "content": "You are a senior reviewer. Output JSON only in a ```json fence."},
        {"role": "user", "content": user},
    ]
    model = models.models["reviewer"]
    opt = models.options.get("reviewer", {})
    content = chat(
        models.ollama_base_url,
        model,
        messages,
        temperature=float(opt.get("temperature", 0.1)),
        num_ctx=int(opt.get("num_ctx", 16384)) if opt.get("num_ctx") else None,
    )
    parsed = extract_json_object(content)
    append_trace(trace_path, "review", {"verdict": parsed.get("verdict")})
    out_path = paths.logs_dir / "last-review.json"
    out_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
    return {"review": parsed, "path": str(out_path)}
