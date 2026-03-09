# T-016: Add Sync-After-Edit-Batches Rule

## Metadata

- Status: `done`
- Created: `2026-03-09`
- Last Updated: `2026-03-09`
- Related Backlog Item: `T-016`
- Related Modules: `AGENTS.md`, `docs/system-checklist.md`

## Context

IDE file refresh behavior was observed to be inconsistent after filesystem edits unless explicit `sync` was run.
To improve collaboration reliability, this operational rule is documented in project instructions.

## Scope

In scope:

- Add rule to run `sync` after filesystem edit batches and before completion reporting.
- Track this as a dedicated task and close it immediately after user confirmation.

Out of scope:

- Any architecture or code behavior changes.

## Acceptance Criteria

- [x] Rule added to `AGENTS.md`.
- [x] Rule already applied in agent execution flow.
- [x] Task tracked and closed on explicit user instruction.

## Implementation Notes

- This is an operational/workflow reliability improvement.
- It is intentionally tracked despite being project-process focused (not product functionality).

## Validation Evidence

- Command(s) run:
  - `sync`
  - `git status --short`
- Manual checks:
  - User confirmed desired behavior and requested tasking + immediate close.
- Output summary:
  - Rule documented and task closed as requested.

## Change Log

- `2026-03-09` - Created and closed task after adding sync-after-edit-batches rule.
