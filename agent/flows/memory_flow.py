"""Memory flow — repo summary and convention files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..config_loader import AgentPaths, ModelsConfig
from ..jsonutil import extract_json_object
from ..llm import complete_chat
from ..repo_context import list_repo_files, tree_summary
from ..trace import append_trace


def run_memory_update(
    root: Path,
    paths: AgentPaths,
    models: ModelsConfig,
    ws: Any,
    *,
    trace_path: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Generate or refresh memory/repo-summary.md from repo listing + model.

    If ``dry_run`` is True, compute ``meta`` and rendered body but do not write the file.
    """
    scan = getattr(ws, "repo_scan", {}) or {}
    ignores = scan.get("ignore_globs", [])
    max_f = int(scan.get("max_files_listed", 400))
    files = list_repo_files(root, ignores, max_f)
    snap = tree_summary(files)

    template = (paths.prompts_dir / "memory.generator.md").read_text(encoding="utf-8")
    user = f"""
{template}

## File list
{snap}
"""
    messages = [
        {"role": "system", "content": "You produce JSON describing the repo. Use a ```json fence."},
        {"role": "user", "content": user},
    ]
    content = complete_chat(root, models, "memory", messages)
    meta = extract_json_object(content)

    out = paths.memory_dir / "repo-summary.md"
    body = _render_repo_summary(meta)
    if dry_run:
        append_trace(trace_path, "memory_update", {"dry_run": True})
        return {
            "path": str(out),
            "meta": meta,
            "dry_run": True,
            "body_preview": body[:8000],
        }

    out.write_text(body, encoding="utf-8")
    append_trace(trace_path, "memory_update", {"path": str(out)})
    return {"path": str(out), "meta": meta, "dry_run": False}


def _render_repo_summary(meta: dict[str, Any]) -> str:
    lines = [
        "# Repository summary (generated)",
        "",
        f"**Purpose:** {meta.get('purpose', '')}",
        "",
        "## Layout",
        "",
    ]
    for item in meta.get("layout", []) or []:
        if isinstance(item, str):
            lines.append(f"- {item}")
        elif isinstance(item, dict):
            lines.append(f"- **{item.get('name')}**: {item.get('description', '')}")
    lines.extend(["", "## Conventions", ""])
    for c in meta.get("conventions", []) or []:
        lines.append(f"- {c}")
    lines.extend(["", "## Tech stack", ""])
    for t in meta.get("tech_stack", []) or []:
        lines.append(f"- {t}")
    lines.extend(["", "## Notes for agents", ""])
    lines.append(meta.get("agent_notes", "(none)"))
    lines.extend(["", "---", "", "*Regenerate with `./scripts/memory-update.sh` or `python3 -m agent memory`*"])
    return "\n".join(lines)
