"""Planner flow — structured plan with read vs write phases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .. import jsonutil
from ..config_loader import AgentPaths, ModelsConfig, WorkspaceConfig
from ..llm import complete_chat
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

    prompt_name = task.get("planner_prompt", "planner.md")
    prompt_path = paths.prompts_dir / prompt_name
    if not prompt_path.is_file():
        prompt_path = paths.prompts_dir / "planner.md"
    planner_template = prompt_path.read_text(encoding="utf-8")

    repo_snapshot = task.get("repo_snapshot", "")
    user_goal = task.get("description", task.get("goal", ""))

    messages = [
        {
            "role": "system",
            "content": (
                "You output only valid JSON in a fenced ```json block. "
                "No prose outside the fence unless the template explicitly allows extra sections inside JSON."
            ),
        },
        {
            "role": "user",
            "content": (
                f"\n{planner_template}\n\n## Skill\n{skill_body}\n\n"
                f"## Repo snapshot\n{repo_snapshot}\n\n## Task\n{user_goal}\n"
            ),
        },
    ]

    content = complete_chat(root, models, "planner", messages)

    plan = jsonutil.extract_json_object(content)
    append_trace(
        trace_path,
        "plan_created",
        {"task_id": task.get("id"), "steps": len(plan.get("steps", []))},
    )

    paths.plans_dir.mkdir(parents=True, exist_ok=True)
    tid = task.get("id", "task")
    plan_file = paths.plans_dir / f"{tid}.plan.json"
    plan_file.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    md_path = paths.plans_dir / f"{tid}.plan.md"
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
        if isinstance(ph, dict):
            lines.append(
                f"- **{ph.get('name')}** ({ph.get('mode', 'read-only')}): {ph.get('description', '')}"
            )
        else:
            lines.append(f"- {ph}")
    lines.extend(["", "## Steps", ""])
    for i, st in enumerate(plan.get("steps", []), 1):
        if not isinstance(st, dict):
            lines.append(f"{i}. {st}")
            lines.append("")
            continue
        mode = st.get("mode", "read-only")
        risk = st.get("risk", "low")
        lines.append(f"{i}. [{mode}] ({risk}) {st.get('title', 'step')}")
        lines.append(f"   - Intent: {st.get('intent', '')}")
        if st.get("validation"):
            lines.append(f"   - Validation: `{st.get('validation')}`")
        lines.append("")

    sf = plan.get("security_findings")
    if isinstance(sf, list) and sf:
        lines.extend(["## Security findings", ""])
        for item in sf:
            if isinstance(item, dict):
                sev = item.get("severity", "?")
                area = item.get("area", "")
                detail = item.get("detail", "")
                lines.append(f"- **[{sev}]** {area}: {detail}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    rr = plan.get("refactor_recommendations")
    if isinstance(rr, list) and rr:
        lines.extend(["## Refactor recommendations", ""])
        for item in rr:
            if isinstance(item, dict):
                title = item.get("title", "")
                rationale = item.get("rationale", "")
                effort = item.get("effort", "")
                lines.append(f"- **{title}** ({effort}): {rationale}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.extend(["## Risks & open questions", ""])
    for r in plan.get("risks", []):
        lines.append(f"- {r}")

    ro = plan.get("read_only_analysis")
    if ro:
        lines.extend(["", "## Read-only analysis", "", str(ro)])

    en = plan.get("execution_notes")
    if en:
        lines.extend(["", "## Execution notes", "", str(en)])

    return "\n".join(lines)
