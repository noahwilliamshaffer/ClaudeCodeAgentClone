# Skill: test-generation

## Goal

Add tests that are **stable**, **fast**, and **aligned with existing patterns**.

## Method

1. Find current test framework and conventions.
2. Add the smallest tests that fail without the fix/feature and pass with it.
3. Avoid brittle full-app integration unless already the norm.

## Guardrails

- No sleeps/waits unless necessary; prefer deterministic fixtures.
- Do not weaken assertions to force green.
