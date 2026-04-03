# Skill: bug-fixing

## Goal

Fix the defect with a **tight hypothesis** and **regression protection**.

## Method

1. Reproduce (or explain why not reproducible locally).
2. Isolate: likely file/function; add logging only if necessary.
3. Fix root cause, not symptoms.
4. Add a test or a minimal check when feasible.

## Guardrails

- Prefer targeted changes over wide rewrites.
- Document flaky reproduction as risk in review.
