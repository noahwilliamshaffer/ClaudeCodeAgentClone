"""Explicit agent pipeline: intake → scan → plan → select → execute → validate → review → memory → decide."""

from __future__ import annotations

from .runner import run_pipeline
from .stages import PIPELINE_STAGES

__all__ = ["PIPELINE_STAGES", "run_pipeline"]
