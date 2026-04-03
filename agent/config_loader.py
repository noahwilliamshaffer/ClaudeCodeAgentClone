"""Load JSON config from the workspace /config directory."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@dataclass
class WorkspaceConfig:
    workspace_name: str
    default_task_path: str
    plan_output_dir: str
    trace_log: str
    repo_scan: dict[str, Any]
    execution: dict[str, Any]


@dataclass
class ModelsConfig:
    ollama_base_url: str
    models: dict[str, str]
    options: dict[str, dict[str, Any]]
    ollama_host_env: str = "OLLAMA_HOST"


@dataclass
class GuardrailsConfig:
    deny_path_globs: list[str]
    warn_path_globs: list[str]
    blocked_command_substrings: list[str]
    require_execute_flag_for_destructive: bool
    max_file_bytes_write: int
    max_files_per_step: int


@dataclass
class AgentPaths:
    """Resolved paths relative to workspace root."""

    root: Path
    config_dir: Path
    memory_dir: Path
    prompts_dir: Path
    skills_dir: Path
    tasks_dir: Path
    logs_dir: Path
    plans_dir: Path


def load_paths(root: Path) -> AgentPaths:
    ws = _read_json(root / "config" / "workspace.json")
    plan_dir = ws.get("plan_output_dir", "memory/plans")
    return AgentPaths(
        root=root,
        config_dir=root / "config",
        memory_dir=root / "memory",
        prompts_dir=root / "prompts",
        skills_dir=root / "skills",
        tasks_dir=root / "tasks",
        logs_dir=root / "logs",
        plans_dir=root / plan_dir,
    )


def load_workspace(root: Path) -> WorkspaceConfig:
    d = _read_json(root / "config" / "workspace.json")
    return WorkspaceConfig(
        workspace_name=d["workspace_name"],
        default_task_path=d["default_task_path"],
        plan_output_dir=d["plan_output_dir"],
        trace_log=d["trace_log"],
        repo_scan=d.get("repo_scan", {}),
        execution=d.get("execution", {}),
    )


def load_models(root: Path) -> ModelsConfig:
    d = _read_json(root / "config" / "models.json")
    return ModelsConfig(
        ollama_base_url=d.get("ollama_base_url", "http://127.0.0.1:11434"),
        models=d["models"],
        options=d.get("options", {}),
        ollama_host_env=str(d.get("ollama_host_env", "OLLAMA_HOST")),
    )


def load_guardrails(root: Path) -> GuardrailsConfig:
    d = _read_json(root / "config" / "guardrails.json")
    return GuardrailsConfig(
        deny_path_globs=d.get("deny_path_globs", []),
        warn_path_globs=d.get("warn_path_globs", []),
        blocked_command_substrings=d.get("blocked_command_substrings", []),
        require_execute_flag_for_destructive=d.get(
            "require_execute_flag_for_destructive", True
        ),
        max_file_bytes_write=int(d.get("max_file_bytes_write", 524288)),
        max_files_per_step=int(d.get("max_files_per_step", 16)),
    )
