"""Executor flow — one step at a time, dry-run by default."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from ..config_loader import AgentPaths, GuardrailsConfig, ModelsConfig, WorkspaceConfig
from ..guardrails import check_command, check_file_size, check_write_path
from ..jsonutil import extract_json_object
from ..llm import complete_chat
from ..skills import load_skill
from ..trace import append_trace


def run_executor(
    root: Path,
    paths: AgentPaths,
    ws: WorkspaceConfig,
    models: ModelsConfig,
    guard: GuardrailsConfig,
    plan: dict[str, Any],
    task: dict[str, Any],
    *,
    step_index: int,
    dry_run: bool,
    execute_writes: bool,
    trace_path: Path,
) -> dict[str, Any]:
    steps = plan.get("steps", [])
    if step_index < 0 or step_index >= len(steps):
        return {"ok": False, "error": f"Invalid step_index {step_index} (len={len(steps)})"}

    step = steps[step_index]
    skill_id = task.get("skill", "feature-implementation")
    skill_body = load_skill(paths.skills_dir, skill_id)

    executor_prompt = (paths.prompts_dir / "executor.md").read_text(encoding="utf-8")
    repo_snapshot = task.get("repo_snapshot", "")

    user = f"""
{executor_prompt}

## Skill
{skill_body}

## Plan context
{json.dumps(plan.get('summary', ''), indent=2)}

## Current step only (execute this step)
{json.dumps(step, indent=2)}

## Repository snapshot (truncated)
{repo_snapshot}

Respond with JSON only (fenced ```json) matching this schema:
{{
  "explanation": "what you will do and why",
  "actions": [
    {{"type": "write_file", "path": "relative/path", "content": "full new file content"}},
    {{"type": "run_command", "command": "pytest -q", "cwd": "."}}
  ],
  "validation_suggestion": "command to verify this step"
}}
Rules:
- Prefer small, incremental changes.
- Paths must be relative to repo root.
- Do not include secrets or edit .env files.
"""

    messages = [
        {"role": "system", "content": "You are a careful coding agent. Output JSON in a ```json fence."},
        {"role": "user", "content": user},
    ]

    content = complete_chat(root, models, "executor", messages)

    parsed = extract_json_object(content)
    actions = parsed.get("actions", [])
    if len(actions) > guard.max_files_per_step:
        return {
            "ok": False,
            "error": f"Too many actions ({len(actions)} > {guard.max_files_per_step})",
            "raw": parsed,
        }

    exe_cfg = ws.execution or {}
    backup_dir = root / exe_cfg.get("backup_dir", "logs/backups")
    backup_on = bool(exe_cfg.get("backup_on_write", True))

    results: list[dict[str, Any]] = []
    for a in actions:
        t = a.get("type")
        if t == "write_file":
            rel = a.get("path", "")
            target = (root / rel).resolve()
            gr = check_write_path(target, root, guard)
            if not gr.ok:
                results.append({"action": a, "ok": False, "error": gr.reason})
                continue
            content_str = a.get("content", "")
            grs = check_file_size(len(content_str.encode("utf-8")), guard)
            if not grs.ok:
                results.append({"action": a, "ok": False, "error": grs.reason})
                continue

            if dry_run or not execute_writes:
                results.append(
                    {
                        "action": a,
                        "ok": True,
                        "dry_run": True,
                        "would_write": rel,
                        "bytes": len(content_str.encode("utf-8")),
                    }
                )
                continue

            if backup_on and target.is_file():
                backup_dir.mkdir(parents=True, exist_ok=True)
                stamp = time.strftime("%Y%m%dT%H%M%S")
                bp = backup_dir / f"{rel.replace('/', '__')}.{stamp}.bak"
                shutil.copy2(target, bp)

            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content_str, encoding="utf-8")
            results.append({"action": a, "ok": True, "written": rel})

        elif t == "run_command":
            cmd = a.get("command", "")
            gc = check_command(cmd, guard)
            if not gc.ok:
                results.append({"action": a, "ok": False, "error": gc.reason})
                continue
            if dry_run or not execute_writes:
                results.append({"action": a, "ok": True, "dry_run": True, "would_run": cmd})
                continue
            cwd = root / (a.get("cwd") or ".")
            cp = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
            )
            results.append(
                {
                    "action": a,
                    "ok": cp.returncode == 0,
                    "returncode": cp.returncode,
                    "stdout": cp.stdout[-8000:],
                    "stderr": cp.stderr[-8000:],
                }
            )
        else:
            results.append({"action": a, "ok": False, "error": f"Unknown action type: {t}"})

    append_trace(
        trace_path,
        "executor_step",
        {
            "step_index": step_index,
            "dry_run": dry_run,
            "execute_writes": execute_writes,
            "results": [{"ok": r.get("ok") for r in results}],
        },
    )

    return {
        "ok": all(r.get("ok") for r in results) if results else True,
        "parsed": parsed,
        "results": results,
    }


def run_task_validations(
    root: Path, task: dict[str, Any], guard: GuardrailsConfig, trace_path: Path
) -> dict[str, Any]:
    cmds = task.get("validation", [])
    out: list[dict[str, Any]] = []
    for cmd in cmds:
        gc = check_command(cmd, guard)
        if not gc.ok:
            out.append({"command": cmd, "ok": False, "error": gc.reason})
            continue
        cp = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True)
        out.append(
            {
                "command": cmd,
                "ok": cp.returncode == 0,
                "returncode": cp.returncode,
                "stdout": cp.stdout[-8000:],
                "stderr": cp.stderr[-8000:],
            }
        )
    append_trace(trace_path, "validation", {"commands": [o.get("command") for o in out]})
    return {"ok": all(o.get("ok") for o in out), "runs": out}
