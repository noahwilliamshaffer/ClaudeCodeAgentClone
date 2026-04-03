# Skill: command-safety

## Goal

Ensure shell commands are **safe**, **portable**, and **non-interactive**.

## Rules

- Prefer explicit paths; quote variables.
- Avoid `rm -rf` on broad globs; never target `/` or system paths.
- For destructive operations, require explicit human confirmation outside automation.
- Use `set -euo pipefail` in bash scripts when appropriate.

## Output

When proposing commands, include a one-line **risk note**.
