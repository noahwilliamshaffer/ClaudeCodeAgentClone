"""Repository snapshot for planning (lightweight, local-first)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def _git_available(root: Path) -> bool:
    return (root / ".git").is_dir()


def list_repo_files(root: Path, ignore_globs: list[str], max_files: int) -> list[str]:
    """Prefer `git ls-files`; fall back to walking the tree."""
    files: list[str] = []
    if _git_available(root):
        try:
            out = subprocess.run(
                ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                capture_output=True,
                check=True,
            )
            raw = out.stdout.split(b"\0")
            for b in raw:
                if not b:
                    continue
                p = b.decode("utf-8", errors="replace")
                if _ignored(p, ignore_globs):
                    continue
                files.append(p)
                if len(files) >= max_files:
                    break
            files.sort()
            return files
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    # Fallback: limited walk
    for dirpath, dirnames, filenames in os_walk_skip(root, ignore_globs):
        for name in filenames:
            rel = Path(dirpath).relative_to(root).as_posix()
            rel_path = f"{rel}/{name}" if rel != "." else name
            if _ignored(rel_path, ignore_globs):
                continue
            files.append(rel_path)
            if len(files) >= max_files:
                files.sort()
                return files
    files.sort()
    return files


def _ignored(rel_posix: str, globs: list[str]) -> bool:
    import fnmatch

    for g in globs:
        if fnmatch.fnmatch(rel_posix, g):
            return True
    return False


def os_walk_skip(root: Path, ignore_globs: list[str]):
    """Yield (dirpath, dirnames, filenames) pruning noisy dirs."""
    import os

    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

    for dirpath, dirnames, filenames in os.walk(root):
        p = Path(dirpath)
        # prune
        dirnames[:] = [
            d
            for d in dirnames
            if d not in skip_dirs
            and not _ignored((p / d).relative_to(root).as_posix(), ignore_globs)
        ]
        yield dirpath, dirnames, filenames


def tree_summary(files: list[str], max_lines: int = 120) -> str:
    lines = ["Repository file list (truncated):"]
    for i, f in enumerate(files[:max_lines]):
        lines.append(f"  - {f}")
    if len(files) > max_lines:
        lines.append(f"  ... ({len(files) - max_lines} more paths omitted)")
    return "\n".join(lines)


def read_text_file(path: Path, max_bytes: int = 120_000) -> str:
    data = path.read_bytes()
    if len(data) > max_bytes:
        return data[:max_bytes].decode("utf-8", errors="replace") + "\n\n[truncated]"
    return data.decode("utf-8", errors="replace")


def load_task_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
