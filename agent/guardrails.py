"""Path and command safety checks — conservative defaults."""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass
from pathlib import Path

from .config_loader import GuardrailsConfig


@dataclass
class GuardResult:
    ok: bool
    reason: str = ""


def _normalize_rel(path: Path, root: Path) -> Path:
    try:
        return path.resolve().relative_to(root.resolve())
    except ValueError:
        return Path(os.path.relpath(path.resolve(), root.resolve()))


def is_under_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def match_any_glob(rel_posix: str, patterns: list[str]) -> bool:
    """
    Match repo-relative POSIX paths against glob patterns.

    ``fnmatch`` does not treat ``**`` as recursive; patterns like ``**/.env`` are handled
    explicitly so nested ``dir/.env`` paths match.
    """
    for p in patterns:
        if fnmatch.fnmatch(rel_posix, p):
            return True
        if p.startswith("**/"):
            suffix = p[3:]
            if suffix and (rel_posix == suffix or rel_posix.endswith("/" + suffix)):
                return True
    return False


def check_write_path(path: Path, root: Path, cfg: GuardrailsConfig) -> GuardResult:
    if not is_under_root(path, root):
        return GuardResult(False, "Path escapes workspace root")
    rel = _normalize_rel(path, root).as_posix()
    if match_any_glob(rel, cfg.deny_path_globs):
        return GuardResult(False, f"Path matches deny glob: {rel}")
    if match_any_glob(rel, cfg.warn_path_globs):
        return GuardResult(False, f"Secrets-sensitive path (blocked by default): {rel}")
    return GuardResult(True)


def check_command(cmd: str, cfg: GuardrailsConfig) -> GuardResult:
    s = cmd.strip()
    low = s.lower()
    if "rm " in low and " -rf" in low and "--no-preserve-root" in low:
        return GuardResult(False, "Blocked destructive rm pattern")
    for b in cfg.blocked_command_substrings:
        if b in s:
            return GuardResult(False, f"Blocked substring: {b!r}")
    return GuardResult(True)


def check_file_size(nbytes: int, cfg: GuardrailsConfig) -> GuardResult:
    if nbytes > cfg.max_file_bytes_write:
        return GuardResult(
            False,
            f"Write too large ({nbytes} bytes > {cfg.max_file_bytes_write})",
        )
    return GuardResult(True)
