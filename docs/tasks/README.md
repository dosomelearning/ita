# Task Tracking Rules

This file defines the canonical task/backlog workflow for this repository.

## Source of Truth

- Active backlog: [`../system-checklist.md`](../system-checklist.md)
- Completed work history: git log and commit messages

## ID System

- Use one ID namespace only: `T-###`
- Example IDs: `T-001`, `T-002`, `T-010`
- The next ID is always derived from `Last Issued ID` in `docs/system-checklist.md`

## Backlog Statuses

Allowed values:

- `todo`
- `in_progress`
- `blocked`
- `done`

`done` is a controlled transition state and may be set only on explicit user instruction.

## Workflow

1. On every new requested task, add a backlog row in `docs/system-checklist.md` with the next `T-###` ID and status `todo`.
2. When implementation starts, switch status to `in_progress`.
3. If blocked, switch status to `blocked` and add a short blocker note.
4. When implementation is ready to close, ask user explicitly whether to set the task to `done`.
5. Only after explicit user instruction, set status to `done`.
6. Choose commit intent and tag commit subject accordingly:
   - `[checkpoint]` for partial/in-progress synchronization commits.
   - `[close]` for closure commits.
7. Commit requirements:
   - `[checkpoint]`: task can be `todo`, `in_progress`, or `blocked`; keep task in active backlog.
   - `[close]`: task must be `done`; remove task row from active backlog in the same commit.
8. Include all relevant `T-###` IDs in commit message body.
9. After commit, run `git status` and report remaining changes.

## Detailed Task Docs

Create a file in `docs/tasks/` only when a backlog item needs deeper design/implementation detail.

- Naming convention: `T-###-short-kebab-title.md`
- Must include metadata and `Related Backlog Item: T-###`
- Keep details concise; backlog remains the operational dashboard
