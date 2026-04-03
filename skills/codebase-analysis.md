# Skill: codebase-analysis

## Goal

Build an accurate mental model of the repository **without modifying files**.

## Method

1. Identify entrypoints (`README`, `pyproject.toml`, `package.json`, `main`, `cli`).
2. Map major directories and responsibilities.
3. Note build/test commands if discoverable from configs.
4. List top risks (complexity, missing tests, global state).

## Output expectations

Prefer structured bullets and explicit "unknowns" over speculation.
