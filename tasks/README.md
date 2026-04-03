# Tasks

Tasks are JSON files consumed by the orchestrator.

## Fields

| Field | Description |
|-------|-------------|
| `id` | Stable identifier (used for plan filenames) |
| `title` | Short title |
| `description` | Goal / acceptance criteria |
| `skill` | Skill id (filename in `/skills` without `.md`) |
| `validation` | Optional list of shell commands to run after changes |

## Example

See `tasks/example-feature.task.json` and `tasks/example-bugfix.task.json`.
