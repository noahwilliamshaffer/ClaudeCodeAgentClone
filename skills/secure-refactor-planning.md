# Skill: secure-refactor-planning

## Goal

Produce a **structured, security-aware refactor plan** from repository context **without** executing changes unless a separate execution phase is explicitly authorized.

## Method

1. **Inventory** sensitive operations: subprocess, file I/O on user paths, network clients, deserialization, shell glue.
2. **Classify** findings by severity with concrete areas (which directories or patterns suggest risk).
3. **Recommend** refactors that improve safety **incrementally** (typing, wrappers, least privilege, validation at boundaries).
4. **Sequence** work so each step is reviewable and testable.

## Output discipline

- Distinguish **confirmed** issues from **hypotheses** when the snapshot lacks file contents.
- Never prescribe bulk deletion of files or mass permission changes as a first step.
- Align JSON fields with `prompts/planner.secure-refactor.md`.
