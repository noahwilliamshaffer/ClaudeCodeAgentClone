"""Next-step decision: structured JSON from LLM with heuristic fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config_loader import AgentPaths, ModelsConfig
from ..jsonutil import extract_json_object
from ..llm import complete_chat
from ..trace import append_trace
from .state import PipelineStateData


def _heuristic_decide(data: PipelineStateData) -> dict[str, Any]:
    plan = data.plan or {}
    steps = plan.get("steps") or []
    idx = int(data.selected_step_index)
    ex_block = data.execution or {}
    result = ex_block.get("result") or {}
    last_ok = bool(result.get("ok", True)) if ex_block else True

    if not steps:
        return {
            "decision": "complete",
            "next_step_index": 0,
            "rationale": "Plan has no steps.",
        }

    if not last_ok:
        return {
            "decision": "stop",
            "next_step_index": idx,
            "rationale": "Last execution reported failure; stop for human review.",
        }

    if idx + 1 < len(steps):
        return {
            "decision": "continue",
            "next_step_index": idx + 1,
            "rationale": "More plan steps remain; advance to next index.",
        }

    rev = (data.review or {}).get("review") or {}
    verdict = str(rev.get("verdict", "")).lower()
    if verdict == "needs_follow_up":
        return {
            "decision": "stop",
            "next_step_index": idx,
            "rationale": "Reviewer requested follow-up; stop for human input.",
        }

    return {
        "decision": "complete",
        "next_step_index": idx,
        "rationale": "Final step completed and review did not require follow-up.",
    }


def run_decide(
    root: Path,
    paths: AgentPaths,
    models: ModelsConfig,
    data: PipelineStateData,
    *,
    trace_path: Path,
    use_llm: bool = True,
) -> dict[str, Any]:
    """
    Set ``data.decision`` to a structured dict: decision, next_step_index, rationale.

    Tries LLM using ``prompts/decide.next.md`` and role ``decide``; on any error, uses heuristic.
    """
    template = (paths.prompts_dir / "decide.next.md").read_text(encoding="utf-8")
    plan_summary = (data.plan or {}).get("summary", "")
    steps = (data.plan or {}).get("steps") or []
    review_blob = data.review or {}
    ex_res = (data.execution or {}).get("result") or {}

    user = f"""
{template}

## Context (machine-readable)

### Task id
{data.task.get("id", "")}

### Current step index
{data.selected_step_index}

### Plan step count
{len(steps)}

### Last execution ok
{ex_res.get("ok", True)}

### Plan summary
{plan_summary}

### Review payload (truncated)
{str(review_blob)[:12000]}
"""

    messages = [
        {
            "role": "system",
            "content": "You output only JSON in a ```json fence. No extra prose.",
        },
        {"role": "user", "content": user},
    ]

    out: dict[str, Any]
    if use_llm and "decide" in models.models:
        try:
            content = complete_chat(root, models, "decide", messages)
            parsed = extract_json_object(content)
            decision = str(parsed.get("decision", "")).lower()
            nxt = int(parsed.get("next_step_index", 0))
            if decision not in ("continue", "complete", "stop"):
                raise ValueError("invalid decision")
            if steps and not (0 <= nxt < len(steps)) and decision == "continue":
                raise ValueError("next_step_index out of range")
            out = {
                "decision": decision,
                "next_step_index": nxt,
                "rationale": str(parsed.get("rationale", "")),
                "source": "llm",
            }
        except Exception:
            out = dict(_heuristic_decide(data))
            out["source"] = "heuristic_fallback"
    else:
        out = dict(_heuristic_decide(data))
        out["source"] = "heuristic"

    data.decision = out
    append_trace(trace_path, "pipeline_decide", {"decision": out.get("decision")})
    return out
