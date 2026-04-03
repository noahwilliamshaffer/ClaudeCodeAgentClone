"""
OpenCode CLI adapter — isolated layer so orchestration stays provider-agnostic.

Uses `opencode run` when OPENCODE_RUNTIME=1 or when --via-opencode is passed.
Falls back to direct Ollama from ollama_client otherwise.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Sequence


def opencode_available() -> bool:
    return shutil.which("opencode") is not None


def build_opencode_env(workspace_root: Path, extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    # Project-local config merge: root opencode.json is discoverable by cwd.
    env.setdefault("OPENCODE_DISABLE_AUTOCOMPACT", "0")
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
    Run: opencode run -m ollama/MODEL ... --file f1 --file f2 "prompt"
    Model should be like 'qwen2.5-coder:latest' (Ollama tag); we prefix ollama/.
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


def should_use_opencode() -> bool:
    return os.environ.get("OPENCODE_RUNTIME", "").strip() in ("1", "true", "yes")
