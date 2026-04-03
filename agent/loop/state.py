"""Structured pipeline state (JSON-serializable) passed between stages."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class PipelineStateData:
    """Pipeline state persisted as JSON between stages and CLI invocations."""

    version: int = STATE_VERSION
    run_id: str = ""
    safe_mode: bool = False
    task_path: str = ""
    current_stage: str = ""
    task: dict[str, Any] = field(default_factory=dict)
    intake: dict[str, Any] = field(default_factory=dict)
    repo_scan: dict[str, Any] = field(default_factory=dict)
    plan: dict[str, Any] = field(default_factory=dict)
    plan_paths: dict[str, str] = field(default_factory=dict)
    selected_step_index: int = 0
    execution: dict[str, Any] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)
    review: dict[str, Any] = field(default_factory=dict)
    memory: dict[str, Any] = field(default_factory=dict)
    decision: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_json_dict(d: dict[str, Any]) -> PipelineStateData:
        v = int(d.get("version", STATE_VERSION))
        if v > STATE_VERSION:
            raise ValueError(f"Unsupported pipeline state version: {v}")
        return PipelineStateData(
            version=v,
            run_id=str(d.get("run_id") or new_run_id()),
            safe_mode=bool(d.get("safe_mode", False)),
            task_path=str(d.get("task_path", "")),
            current_stage=str(d.get("current_stage", "")),
            task=dict(d.get("task") or {}),
            intake=dict(d.get("intake") or {}),
            repo_scan=dict(d.get("repo_scan") or {}),
            plan=dict(d.get("plan") or {}),
            plan_paths=dict(d.get("plan_paths") or {}),
            selected_step_index=int(d.get("selected_step_index", 0)),
            execution=dict(d.get("execution") or {}),
            validation=dict(d.get("validation") or {}),
            review=dict(d.get("review") or {}),
            memory=dict(d.get("memory") or {}),
            decision=dict(d.get("decision") or {}),
            history=list(d.get("history") or []),
        )


def new_run_id() -> str:
    return str(uuid.uuid4())


def default_state_path(root: Path, task_id: str, run_id: str) -> Path:
    short = run_id.split("-")[0] if run_id else "run"
    return root / "memory" / "runs" / f"{task_id}-{short}.json"


def save_state(path: Path, data: PipelineStateData) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data.to_json_dict(), indent=2), encoding="utf-8")


def load_state(path: Path) -> PipelineStateData:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return PipelineStateData.from_json_dict(raw)


def append_history(
    data: PipelineStateData,
    stage: str,
    ok: bool,
    error: str | None = None,
    **notes: Any,
) -> None:
    rec: dict[str, Any] = {"stage": stage, "ok": ok, "ts": utc_now()}
    if error:
        rec["error"] = error
    if notes:
        rec["notes"] = notes
    data.history.append(rec)
