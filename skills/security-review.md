# Skill: security-review

## Goal

Find security issues: **secrets**, **injection**, **unsafe deserialization**, **path traversal**, **shell misuse**.

## Method

1. Scan for secret patterns and unsafe defaults.
2. Review trust boundaries (user input, file paths, subprocess).
3. Prioritize by exploitability and impact.

## Guardrails

- Distinguish confirmed issues from hypotheticals.
- Suggest minimal fixes; avoid large unrelated hardening in one step.
