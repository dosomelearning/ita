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

`done` is not used in the backlog table. Completed items are removed after commit.

## Workflow

1. On every new requested task, add a backlog row in `docs/system-checklist.md` with the next `T-###` ID and status `todo`.
2. When implementation starts, switch status to `in_progress`.
3. If blocked, switch status to `blocked` and add a short blocker note.
4. After implementation is complete and committed, remove the row from the backlog table.
5. Include all relevant `T-###` IDs in the commit message body.

## Detailed Task Docs

Create a file in `docs/tasks/` only when a backlog item needs deeper design/implementation detail.

- Naming convention: `T-###-short-kebab-title.md`
- Must include metadata and `Related Backlog Item: T-###`
- Keep details concise; backlog remains the operational dashboard
