# Documentation Map

This directory keeps project-wide operational documentation that does not belong in module-specific READMEs.

## Files

- [`system-checklist.md`](system-checklist.md) - single source of truth for cross-project tasks and status.
- [`tasks/README.md`](tasks/README.md) - canonical rules for task IDs and backlog workflow.
- [`tasks/TEMPLATE.md`](tasks/TEMPLATE.md) - template for individual detailed task documents.

## Workflow

1. Add/update backlog items in `system-checklist.md` using `T-###` IDs.
2. Follow process rules in `tasks/README.md`.
3. Create a task file in `docs/tasks/` only when an item needs detailed implementation notes.
4. Track completion in git log and commit messages (not in a completed table).

## Status Convention

Allowed status values:

- `todo`
- `in_progress`
- `blocked`

## ID Convention

- Single ID namespace for backlog/tasks: `T-###`
