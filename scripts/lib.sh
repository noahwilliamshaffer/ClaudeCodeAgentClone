#!/usr/bin/env bash
# Shared helpers for workspace scripts.
set -euo pipefail

workspace_root() {
  local here
  here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  echo "$here"
}

export PYTHONPATH="${PYTHONPATH:-}:$(workspace_root)"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "error: required command not found: $1" >&2
    exit 127
  }
}
