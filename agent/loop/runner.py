"""Run the explicit pipeline: single stage, full chain, or multi-step loop."""

from __future__ import annotations

from pathlib import Path

from ..config_loader import load_guardrails, load_models, load_paths, load_workspace
from ..repo_context import load_task_json
from .state import (
    PipelineStateData,
    append_history,
    default_state_path,
    load_state,
    new_run_id,
    save_state,
)
from .stages import PIPELINE_STAGES, RunContext, run_one_stage


def _resolve(root: Path, p: str | Path) -> Path:
    path = Path(p)
    return path if path.is_absolute() else (root / path).resolve()


def _make_ctx(root: Path) -> RunContext:
    ws = load_workspace(root)
    return RunContext(
        root=root,
        paths=load_paths(root),
        ws=ws,
        models=load_models(root),
        guard=load_guardrails(root),
        trace_path=root / ws.trace_log,
    )


def _load_or_create_state(
    root: Path,
    state_path: str | Path | None,
    task_path: str | None,
    safe_mode: bool,
) -> tuple[PipelineStateData, Path]:
    """Return ``(data, path_to_state_file)``."""
    if state_path:
        sp = _resolve(root, state_path)
        if sp.exists():
            data = load_state(sp)
            if safe_mode:
                data.safe_mode = True
            return data, sp
        if not task_path:
            raise FileNotFoundError(
                f"State file not found: {sp}. Pass --task to create it."
            )
        tp = _resolve(root, task_path)
        task = load_task_json(tp)
        tid = str(task.get("id", "task"))
        rid = new_run_id()
        rel = str(tp.relative_to(root)) if tp.is_relative_to(root) else str(tp)
        data = PipelineStateData(run_id=rid, safe_mode=safe_mode, task_path=rel)
        append_history(data, "init", True, state_path=str(sp))
        return data, sp

    if not task_path:
        raise FileNotFoundError("Provide --task (new run) or --state (existing state file).")

    tp = _resolve(root, task_path)
    task = load_task_json(tp)
    tid = str(task.get("id", "task"))
    rid = new_run_id()
    rel = str(tp.relative_to(root)) if tp.is_relative_to(root) else str(tp)
    data = PipelineStateData(run_id=rid, safe_mode=safe_mode, task_path=rel)
    sp = default_state_path(root, tid, rid)
    append_history(data, "init", True, state_path=str(sp))
    return data, sp


def run_pipeline(
    root: Path,
    *,
    state_path: str | Path | None,
    task_path: str | None,
    safe_mode: bool,
    execute_writes: bool,
    step_index: int | None,
    max_rounds: int,
    single_stage: str | None,
) -> tuple[PipelineStateData, Path, bool]:
    """
    Run the pipeline.

    * **single_stage** — run exactly one stage and return.
    * Otherwise — run ``intake → scan → plan → select`` then repeat
      ``execute → validate → review → memory → decide`` until the decision is not
      ``continue`` or ``max_rounds`` is reached. After each ``continue``, ``select``
      runs with ``decision.next_step_index``.

    Returns ``(data, state_file_path, ok)``.
    """
    ctx = _make_ctx(root)
    data, sp = _load_or_create_state(root, state_path, task_path, safe_mode)

    if safe_mode:
        data.safe_mode = True
    sm = bool(data.safe_mode)
    ew = bool(execute_writes) and not sm

    if single_stage:
        if single_stage not in PIPELINE_STAGES:
            raise ValueError(f"Unknown stage {single_stage!r}; expected one of {PIPELINE_STAGES}")
        ok = run_one_stage(
            single_stage,
            ctx,
            data,
            safe_mode=sm,
            execute_writes=ew,
            step_index=step_index,
        )
        save_state(sp, data)
        return data, sp, ok

    for name in ("intake", "scan", "plan"):
        if not run_one_stage(name, ctx, data, safe_mode=sm, execute_writes=ew):
            save_state(sp, data)
            return data, sp, False

    sel = 0 if step_index is None else int(step_index)
    if not run_one_stage(
        "select",
        ctx,
        data,
        safe_mode=sm,
        execute_writes=ew,
        step_index=sel,
    ):
        save_state(sp, data)
        return data, sp, False

    save_state(sp, data)

    rounds = 0
    while rounds < max_rounds:
        for name in ("execute", "validate", "review", "memory", "decide"):
            if not run_one_stage(name, ctx, data, safe_mode=sm, execute_writes=ew):
                save_state(sp, data)
                return data, sp, False
        save_state(sp, data)

        dec = str((data.decision or {}).get("decision", "complete")).lower()
        if dec != "continue":
            break

        nxt = int((data.decision or {}).get("next_step_index", 0))
        if not run_one_stage(
            "select",
            ctx,
            data,
            safe_mode=sm,
            execute_writes=ew,
            step_index=nxt,
        ):
            save_state(sp, data)
            return data, sp, False
        save_state(sp, data)
        rounds += 1

    return data, sp, True
