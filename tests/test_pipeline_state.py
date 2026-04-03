"""Pipeline state serialization."""

from __future__ import annotations

import json
from pathlib import Path

from agent.loop.state import PipelineStateData, load_state, new_run_id, save_state


def test_roundtrip(tmp_path: Path):
    p = tmp_path / "s.json"
    d = PipelineStateData(
        run_id=new_run_id(),
        task_path="tasks/x.task.json",
        current_stage="scan",
        task={"id": "t1"},
        repo_scan={"file_count": 3},
    )
    save_state(p, d)
    d2 = load_state(p)
    assert d2.task["id"] == "t1"
    assert d2.repo_scan["file_count"] == 3
    raw = json.loads(p.read_text(encoding="utf-8"))
    assert raw["version"] == 1
