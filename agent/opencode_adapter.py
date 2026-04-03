"""
OpenCode CLI adapter — **isolated** from orchestration logic.

Purpose
-------
The Python orchestrator normally talks to **Ollama** over HTTP (``ollama_client``). When you
set ``OPENCODE_RUNTIME=1``, the same prompts are sent through ``opencode run`` so you can:

- Use OpenCode’s configured providers/models from ``opencode.json``
- Attach files with ``--file`` (see ``opencode_run``)
- Later swap to ``opencode serve`` + HTTP without changing planner/executor code paths

This module does **not** replicate OpenCode’s full agent tool loop; it only substitutes the
**text generation** transport. See ``docs/INTEGRATION-OPENCODE.md`` for the full integration
map and upgrade paths.

Environment
-----------
- ``OPENCODE_RUNTIME``: when ``1``/``true``/``yes``, ``agent.llm.complete_chat`` routes here.
- ``OPENCODE_CONFIG``: optional path to an alternate OpenCode JSON config (standard OpenCode).
- Working directory for ``opencode run`` is always the workspace root so project ``opencode.json`` applies.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Sequence


def opencode_available() -> bool:
    return shutil.which("opencode") is not None


def should_use_opencode() -> bool:
    return os.environ.get("OPENCODE_RUNTIME", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def build_opencode_env(workspace_root: Path, extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("OPENCODE_DISABLE_AUTOCOMPACT", "0")
    # Ensure CWD-dependent discovery sees project config.
    env["PWD"] = str(workspace_root)
    if extra:
        env.update(extra)
    return env


def opencode_run(
    workspace_root: Path,
    prompt: str,
    *,
    model: str,
    attached_files: Sequence[Path] | None = None,
    format_json: bool = False,
) -> subprocess.CompletedProcess[str]:
    """
    Run: ``opencode run -m ollama/<model> [--file ...] "<prompt>"``

    ``model`` may be ``qwen2.5-coder:latest`` or already ``ollama/qwen2.5-coder:latest``.
    """
    oc = shutil.which("opencode")
    if not oc:
        raise RuntimeError("opencode not found in PATH")

    m = model.strip()
    if "/" not in m:
        m = f"ollama/{m}"

    cmd: list[str] = [oc, "run", "-m", m]
    if format_json:
        cmd.extend(["--format", "json"])
    for f in attached_files or []:
        cmd.extend(["--file", str(f)])
    cmd.append(prompt)

    return subprocess.run(
        cmd,
        cwd=workspace_root,
        capture_output=True,
        text=True,
        env=build_opencode_env(workspace_root),
        check=False,
    )


def complete_with_opencode(
    workspace_root: Path,
    prompt: str,
    *,
    model: str,
    temperature: float = 0.2,
) -> str:
    """
    Single-shot completion via OpenCode CLI. Returns stdout text.

    Note: OpenCode may not expose per-request temperature on the CLI; generation parameters
    still follow ``opencode.json`` and provider defaults. The ``temperature`` argument is
    reserved for future env-based wiring and for parity with the Ollama path.
    """
    _ = temperature  # reserved — OpenCode CLI uses project/provider defaults
    proc = opencode_run(workspace_root, prompt, model=model)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"opencode run failed (exit {proc.returncode}): {err}")
    out = (proc.stdout or "").strip()
    if not out:
        raise RuntimeError("opencode returned empty stdout")
    return out
