"""CLI entrypoints: plan, execute, review, memory, loop."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config_loader import (
    load_guardrails,
    load_models,
    load_paths,
    load_workspace,
)
from .env import resolve_ollama_base_url
from .flows.executor import run_executor, run_task_validations
from .flows.memory_flow import run_memory_update
from .flows.planner import run_planner
from .flows.reviewer import run_reviewer
from .repo_context import list_repo_files, load_task_json, tree_summary
from .trace import append_trace


def _root() -> Path:
    # agent/ -> workspace root
    return Path(__file__).resolve().parent.parent


def cmd_plan(args: argparse.Namespace) -> int:
    root = _root()
    paths = load_paths(root)
    ws = load_workspace(root)
    models = load_models(root)
    trace_path = root / ws.trace_log
    task_path = Path(args.task)
    if not task_path.is_absolute():
        task_path = root / task_path
    task = load_task_json(task_path)
    scan = ws.repo_scan or {}
    files = list_repo_files(root, scan.get("ignore_globs", []), int(scan.get("max_files_listed", 400)))
    task["repo_snapshot"] = tree_summary(files)
    res = run_planner(root, paths, ws, models, task, trace_path=trace_path)
    print(json.dumps(res, indent=2))
    return 0


def cmd_execute(args: argparse.Namespace) -> int:
    root = _root()
    paths = load_paths(root)
    ws = load_workspace(root)
    models = load_models(root)
    guard = load_guardrails(root)
    trace_path = root / ws.trace_log
    plan_path = Path(args.plan)
    if not plan_path.is_absolute():
        plan_path = root / plan_path
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    task_path = Path(args.task)
    if not task_path.is_absolute():
        task_path = root / task_path
    task = load_task_json(task_path)
    scan = ws.repo_scan or {}
    files = list_repo_files(root, scan.get("ignore_globs", []), int(scan.get("max_files_listed", 400)))
    task["repo_snapshot"] = tree_summary(files)

    execute_writes = bool(args.force_execute)
    dry_run = not execute_writes

    res = run_executor(
        root,
        paths,
        ws,
        models,
        guard,
        plan,
        task,
        step_index=int(args.step),
        dry_run=dry_run,
        execute_writes=execute_writes,
        trace_path=trace_path,
    )
    print(json.dumps(res, indent=2))
    if args.validate_after and execute_writes:
        val = run_task_validations(root, task, guard, trace_path)
        print(json.dumps({"validation": val}, indent=2))
    return 0 if res.get("ok") else 1


def cmd_review(args: argparse.Namespace) -> int:
    root = _root()
    paths = load_paths(root)
    ws = load_workspace(root)
    models = load_models(root)
    trace_path = root / ws.trace_log
    task_path = Path(args.task)
    if not task_path.is_absolute():
        task_path = root / task_path
    task = load_task_json(task_path)
    plan = None
    if args.plan:
        plan_path = Path(args.plan)
        if not plan_path.is_absolute():
            plan_path = root / plan_path
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    res = run_reviewer(root, paths, models, task, plan, trace_path=trace_path)
    print(json.dumps(res, indent=2))
    return 0


def cmd_memory(args: argparse.Namespace) -> int:
    root = _root()
    paths = load_paths(root)
    ws = load_workspace(root)
    models = load_models(root)
    trace_path = root / ws.trace_log
    res = run_memory_update(root, paths, models, ws, trace_path=trace_path)
    print(json.dumps(res, indent=2))
    return 0


def cmd_loop(args: argparse.Namespace) -> int:
    """Plan → execute all steps (dry-run default) → review → optional validate."""
    root = _root()
    paths = load_paths(root)
    ws = load_workspace(root)
    models = load_models(root)
    guard = load_guardrails(root)
    trace_path = root / ws.trace_log
    append_trace(trace_path, "loop_start", {"task": args.task})

    task_path = Path(args.task)
    if not task_path.is_absolute():
        task_path = root / task_path
    task = load_task_json(task_path)
    scan = ws.repo_scan or {}
    files = list_repo_files(root, scan.get("ignore_globs", []), int(scan.get("max_files_listed", 400)))
    task["repo_snapshot"] = tree_summary(files)

    pres = run_planner(root, paths, ws, models, task, trace_path=trace_path)
    plan = pres["plan"]
    plan_path = Path(pres["json_path"])
    if not plan_path.is_absolute():
        plan_path = root / plan_path
    plan = json.loads(plan_path.read_text(encoding="utf-8"))

    dry_default = bool(ws.execution.get("default_dry_run", True))
    execute_writes = bool(args.force_execute)
    dry_run = not execute_writes and dry_default

    step_results = []
    for i in range(len(plan.get("steps", []))):
        r = run_executor(
            root,
            paths,
            ws,
            models,
            guard,
            plan,
            task,
            step_index=i,
            dry_run=dry_run,
            execute_writes=execute_writes,
            trace_path=trace_path,
        )
        step_results.append(r)

    val = None
    if execute_writes and args.validate_after:
        val = run_task_validations(root, task, guard, trace_path)

    rev = run_reviewer(root, paths, models, task, plan, trace_path=trace_path)
    out = {"plan": pres, "steps": step_results, "validation": val, "review": rev}
    print(json.dumps(out, indent=2))
    ok = all(s.get("ok") for s in step_results) if step_results else True
    append_trace(trace_path, "loop_end", {"ok": ok})
    return 0 if ok else 1


def cmd_doctor(args: argparse.Namespace) -> int:
    """Check Ollama reachability and list a few models."""
    root = _root()
    models = load_models(root)
    from . import llm

    try:
        names = llm.list_local_models(models)
    except Exception as e:
        print(
            json.dumps(
                {"ok": False, "error": str(e), "base_url": resolve_ollama_base_url(models)},
                indent=2,
            )
        )
        return 1

    print(
        json.dumps(
            {
                "ok": True,
                "base_url": resolve_ollama_base_url(models),
                "models": names[:50],
                "model_count": len(names),
            },
            indent=2,
        )
    )
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    root = _root()
    ws = load_workspace(root)
    guard = load_guardrails(root)
    trace_path = root / ws.trace_log
    task_path = Path(args.task)
    if not task_path.is_absolute():
        task_path = root / task_path
    task = load_task_json(task_path)
    val = run_task_validations(root, task, guard, trace_path)
    print(json.dumps(val, indent=2))
    return 0 if val.get("ok") else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agent", description="Local agent workspace orchestrator")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_plan = sub.add_parser("plan", help="Create a structured plan from a task JSON")
    p_plan.add_argument("--task", required=True, help="Path to task JSON")
    p_plan.set_defaults(func=cmd_plan)

    p_ex = sub.add_parser("execute", help="Run one plan step")
    p_ex.add_argument("--task", required=True)
    p_ex.add_argument("--plan", required=True, help="Path to plan JSON")
    p_ex.add_argument("--step", default="0")
    p_ex.add_argument(
        "--force-execute",
        action="store_true",
        help="Apply file writes and run commands (otherwise dry-run)",
    )
    p_ex.add_argument(
        "--validate-after",
        action="store_true",
        help="Run task validation commands after successful execute",
    )
    p_ex.set_defaults(func=cmd_execute)

    p_rev = sub.add_parser("review", help="Reviewer pass")
    p_rev.add_argument("--task", required=True)
    p_rev.add_argument("--plan", default=None)
    p_rev.set_defaults(func=cmd_review)

    p_mem = sub.add_parser("memory", help="Refresh memory/repo-summary.md")
    p_mem.set_defaults(func=cmd_memory)

    p_loop = sub.add_parser("loop", help="Plan + all steps + review (optional validate)")
    p_loop.add_argument("--task", required=True)
    p_loop.add_argument(
        "--force-execute",
        action="store_true",
        help="Actually write files and run commands (otherwise dry-run)",
    )
    p_loop.add_argument(
        "--validate-after",
        action="store_true",
        help="Run validation commands from task JSON after execution",
    )
    p_loop.set_defaults(func=cmd_loop)

    p_val = sub.add_parser("validate", help="Run validation commands from task JSON only")
    p_val.add_argument("--task", required=True)
    p_val.set_defaults(func=cmd_validate)

    p_doc = sub.add_parser("doctor", help="Check Ollama connectivity and list local models")
    p_doc.set_defaults(func=cmd_doctor)

    return p


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
