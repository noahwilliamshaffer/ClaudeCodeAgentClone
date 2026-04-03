# Skill: refactor-review

## Goal

Improve structure/readability while **preserving behavior**.

## Method

1. Identify coupling and duplication with evidence (paths/symbols).
2. Propose incremental steps; keep each step reviewable.
3. Run existing tests after each logical chunk (when available).

## Guardrails

- No behavior change unless explicitly requested.
- Flag any API breaks and migration notes.
