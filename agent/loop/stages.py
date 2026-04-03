"""Individual pipeline stages — each updates :class:`PipelineStateData` in place."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config_loader import AgentPaths, GuardrailsConfig, ModelsConfig, WorkspaceConfig
from ..flows.executor import run_executor, run_task_validations
from ..flows.memory_flow import run_memory_update
from ..flows.planner import run_planner
from ..flows.reviewer import run_reviewer
from ..repo_context import list_repo_files, load_task_json, tree_summary
from ..trace import append_trace
from .decide import run_decide
from .state import PipelineStateData, append_history, utc_now

PIPELINE_STAGES: tuple[str, ...] = (
    "intake",
    "scan",
    "plan",
    "select",
    "execute",
    "validate",
    "review",
    "memory",
    "decide",
)


@dataclass
class RunContext:
    root: Path
    paths: AgentPaths
    ws: WorkspaceConfig
    models: ModelsConfig
    guard: GuardrailsConfig
    trace_path: Path


def _task_path_obj(root: Path, p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else (root / path).resolve()


def stage_intake(ctx: RunContext, data: PipelineStateData) -> bool:
    """Load task JSON into ``data.task`` and record intake metadata."""
    tp = _task_path_obj(ctx.root, data.task_path)
    if not tp.is_file():
        append_history(data, "intake", False, error=f"Task file not found: {tp}")
        return False
    task = load_task_json(tp)
    if not task.get("id"):
        task["id"] = "task"
    data.task = task
    data.intake = {
        "ok": True,
        "task_path": str(tp.relative_to(ctx.root)) if tp.is_relative_to(ctx.root) else str(tp),
        "task_id": task["id"],
        "loaded_at": utc_now(),
    }
    data.current_stage = "intake"
    append_trace(ctx.trace_path, "pipeline_intake", {"task_id": task["id"]})
    append_history(data, "intake", True)
    return True


def stage_scan(ctx: RunContext, data: PipelineStateData) -> bool:
    """Populate ``data.repo_scan`` and attach snapshot text to ``data.task``."""
    scan = ctx.ws.repo_scan or {}
    files = list_repo_files(
        ctx.root,
        scan.get("ignore_globs", []),
        int(scan.get("max_files_listed", 400)),
    )
    summary = tree_summary(files)
    data.repo_scan = {
        "file_count": len(files),
        "files": files[:500],
        "summary_text": summary,
    }
    data.task["repo_snapshot"] = summary
    data.current_stage = "scan"
    append_trace(ctx.trace_path, "pipeline_scan", {"file_count": len(files)})
    append_history(data, "scan", True, file_count=len(files))
    return True


def stage_plan(ctx: RunContext, data: PipelineStateData) -> bool:
    """Run planner; fill ``data.plan`` and ``data.plan_paths``."""
    try:
        res = run_planner(
            ctx.root,
            ctx.paths,
            ctx.ws,
            ctx.models,
            data.task,
            trace_path=ctx.trace_path,
        )
    except Exception as e:
        append_history(data, "plan", False, error=str(e))
        return False
    data.plan = res["plan"]
    data.plan_paths = {
        "json": res["json_path"],
        "markdown": res["markdown_path"],
    }
    data.current_stage = "plan"
    append_history(data, "plan", True)
    return True


def stage_select(
    ctx: RunContext,
    data: PipelineStateData,
    *,
    step_index: int | None = None,
) -> bool:
    """Choose ``data.selected_step_index`` for execution."""
    steps = (data.plan or {}).get("steps") or []
    if step_index is not None:
        idx = int(step_index)
    elif data.decision.get("decision") == "continue" and "next_step_index" in data.decision:
        idx = int(data.decision["next_step_index"])
    else:
        idx = int(data.selected_step_index)

    if steps and not (0 <= idx < len(steps)):
        append_history(data, "select", False, error=f"step_index {idx} out of range (0..{len(steps)-1})")
        return False

    data.selected_step_index = max(0, idx)
    data.current_stage = "select"
    data.execution = {}
    append_trace(ctx.trace_path, "pipeline_select", {"step": data.selected_step_index})
    append_history(data, "select", True, selected_step_index=data.selected_step_index)
    return True


def stage_execute(
    ctx: RunContext,
    data: PipelineStateData,
    *,
    safe_mode: bool,
    execute_writes: bool,
) -> bool:
    """Run executor for ``data.selected_step_index``."""
    plan = data.plan or {}
    if not plan.get("steps"):
        data.execution = {"skipped": True, "reason": "no steps"}
        append_history(data, "execute", True, skipped=True)
        return True

    if safe_mode:
        dry_run = True
        ew = False
    else:
        ew = bool(execute_writes)
        dry_run = not ew

    try:
        result = run_executor(
            ctx.root,
            ctx.paths,
            ctx.ws,
            ctx.models,
            ctx.guard,
            plan,
            data.task,
            step_index=int(data.selected_step_index),
            dry_run=dry_run,
            execute_writes=ew,
            trace_path=ctx.trace_path,
        )
    except Exception as e:
        append_history(data, "execute", False, error=str(e))
        return False

    data.execution = {
        "step_index": data.selected_step_index,
        "result": result,
        "safe_mode": safe_mode,
        "dry_run": dry_run,
        "execute_writes": ew,
    }
    data.current_stage = "execute"
    ok = bool(result.get("ok", True))
    append_history(data, "execute", ok)
    return True


def stage_validate(ctx: RunContext, data: PipelineStateData, *, safe_mode: bool) -> bool:
    """Run task validation commands from ``data.task``."""
    try:
        val = run_task_validations(ctx.root, data.task, ctx.guard, ctx.trace_path)
    except Exception as e:
        append_history(data, "validate", False, error=str(e))
        return False
    data.validation = dict(val)
    if safe_mode:
        data.validation["note"] = "safe_mode: validations are read-only commands from task JSON"
    data.current_stage = "validate"
    append_history(data, "validate", bool(val.get("ok", True)))
    return True


def stage_review(ctx: RunContext, data: PipelineStateData) -> bool:
    """Run reviewer with current plan."""
    try:
        res = run_reviewer(
            ctx.root,
            ctx.paths,
            ctx.models,
            data.task,
            data.plan or None,
            trace_path=ctx.trace_path,
        )
    except Exception as e:
        append_history(data, "review", False, error=str(e))
        return False
    data.review = res
    data.current_stage = "review"
    append_history(data, "review", True)
    return True


def stage_memory(ctx: RunContext, data: PipelineStateData, *, safe_mode: bool) -> bool:
    """Refresh repo summary; skip file write in ``safe_mode``."""
    try:
        mem = run_memory_update(
            ctx.root,
            ctx.paths,
            ctx.models,
            ctx.ws,
            trace_path=ctx.trace_path,
            dry_run=bool(safe_mode),
        )
    except Exception as e:
        append_history(data, "memory", False, error=str(e))
        return False
    data.memory = mem
    data.current_stage = "memory"
    append_history(data, "memory", True, dry_run=bool(mem.get("dry_run")))
    return True


def stage_decide(ctx: RunContext, data: PipelineStateData) -> bool:
    """Set ``data.decision`` for loop control."""
    try:
        run_decide(ctx.root, ctx.paths, ctx.models, data, trace_path=ctx.trace_path)
    except Exception as e:
        append_history(data, "decide", False, error=str(e))
        return False
    data.current_stage = "decide"
    append_history(data, "decide", True)
    return True


def run_one_stage(
    name: str,
    ctx: StageContext,
    data: PipelineStateData,
    *,
    safe_mode: bool,
    execute_writes: bool = False,
    step_index: int | None = None,
) -> bool:
    """Run a single named stage."""
    if name == "intake":
        return stage_intake(ctx, data)
    if name == "scan":
        return stage_scan(ctx, data)
    if name == "plan":
        return stage_plan(ctx, data)
    if name == "select":
        return stage_select(ctx, data, step_index=step_index)
    if name == "execute":
        return stage_execute(ctx, data, safe_mode=safe_mode, execute_writes=execute_writes)
    if name == "validate":
        return stage_validate(ctx, data, safe_mode=safe_mode)
    if name == "review":
        return stage_review(ctx, data)
    if name == "memory":
        return stage_memory(ctx, data, safe_mode=safe_mode)
    if name == "decide":
        return stage_decide(ctx, data)
    raise ValueError(f"Unknown stage: {name}")
