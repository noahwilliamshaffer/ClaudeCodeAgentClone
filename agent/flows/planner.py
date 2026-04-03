"""Planner flow — structured plan with read vs write phases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .. import jsonutil
from ..config_loader import AgentPaths, ModelsConfig, WorkspaceConfig
from ..ollama_client import chat
from ..skills import load_skill
from ..trace import append_trace


def run_planner(
    root: Path,
    paths: AgentPaths,
    ws: WorkspaceConfig,
    models: ModelsConfig,
    task: dict[str, Any],
    *,
    trace_path: Path,
) -> dict[str, Any]:
    skill_id = task.get("skill", "feature-implementation")
    skill_body = load_skill(paths.skills_dir, skill_id)

    prompt_path = paths.prompts_dir / "planner.md"
    planner_template = prompt_path.read_text(encoding="utf-8")

    repo_snapshot = task.get("repo_snapshot", "")
    user_goal = task.get("description", task.get("goal", ""))

    messages = [
        {
            "role": "system",
            "content": "You output only valid JSON in a fenced ```json block. No prose outside the fence.",
        },
        {
            "role": "user",
            "content": f"\n{planner_template}\n\n## Skill\n{skill_body}\n\n## Repo snapshot\n{repo_snapshot}\n\n## Task\n{user_goal}\n",
        },
    ]

    model = models.models["planner"]
    opt = models.options.get("planner", {})
    content = chat(
        models.ollama_base_url,
        model,
        messages,
        temperature=float(opt.get("temperature", 0.2)),
        num_ctx=int(opt.get("num_ctx", 8192)) if opt.get("num_ctx") else None,
    )

    plan = jsonutil.extract_json_object(content)
    append_trace(
        trace_path,
        "plan_created",
        {"task_id": task.get("id"), "steps": len(plan.get("steps", []))},
    )

    paths.plans_dir.mkdir(parents=True, exist_ok=True)
    plan_file = paths.plans_dir / f"{task.get('id', 'task')}.plan.json"
    plan_file.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    md_path = paths.plans_dir / f"{task.get('id', 'task')}.plan.md"
    md_path.write_text(_plan_to_markdown(plan, task), encoding="utf-8")

    return {"plan": plan, "json_path": str(plan_file), "markdown_path": str(md_path)}


def _plan_to_markdown(plan: dict[str, Any], task: dict[str, Any]) -> str:
    lines = [
        f"# Plan: {task.get('title', task.get('id', 'task'))}",
        "",
        f"Summary: {plan.get('summary', '')}",
        "",
        "## Phases",
        "",
    ]
    for ph in plan.get("phases", []):
        lines.append(f"- **{ph.get('name')}** ({ph.get('mode', 'read-only')}): {ph.get('description', '')}")
    lines.extend(["", "## Steps", ""])
    for i, st in enumerate(plan.get("steps", []), 1):
        mode = st.get("mode", "read-only")
        risk = st.get("risk", "low")
        lines.append(f"{i}. [{mode}] ({risk}) {st.get('title', 'step')}")
        lines.append(f"   - Intent: {st.get('intent', '')}")
        if st.get("validation"):
            lines.append(f"   - Validation: `{st.get('validation')}`")
        lines.append("")
    lines.append("## Risks & open questions")
    lines.append("")
    for r in plan.get("risks", []):
        lines.append(f"- {r}")
    return "\n".join(lines)
