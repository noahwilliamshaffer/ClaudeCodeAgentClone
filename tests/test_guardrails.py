"""Tests for agent.guardrails."""

from __future__ import annotations

from pathlib import Path

from agent.config_loader import GuardrailsConfig
from agent.guardrails import check_command, check_write_path


def test_blocks_env_write(tmp_path: Path):
    cfg = GuardrailsConfig(
        deny_path_globs=["**/.env", "**/.env.*"],
        warn_path_globs=[],
        blocked_command_substrings=[],
        require_execute_flag_for_destructive=True,
        max_file_bytes_write=1000,
        max_files_per_step=8,
    )
    p = tmp_path / ".env"
    r = check_write_path(p, tmp_path, cfg)
    assert r.ok is False


def test_allows_safe_path(tmp_path: Path):
    cfg = GuardrailsConfig(
        deny_path_globs=["**/.env"],
        warn_path_globs=[],
        blocked_command_substrings=[],
        require_execute_flag_for_destructive=True,
        max_file_bytes_write=1000,
        max_files_per_step=8,
    )
    p = tmp_path / "src" / "main.py"
    p.parent.mkdir(parents=True)
    r = check_write_path(p, tmp_path, cfg)
    assert r.ok is True


def test_blocked_substring():
    cfg = GuardrailsConfig(
        deny_path_globs=[],
        warn_path_globs=[],
        blocked_command_substrings=["rm -rf /"],
        require_execute_flag_for_destructive=True,
        max_file_bytes_write=1000,
        max_files_per_step=8,
    )
    r = check_command("rm -rf /", cfg)
    assert r.ok is False
