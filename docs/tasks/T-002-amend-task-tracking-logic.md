# T-002: Amend Task Tracking Logic

## Metadata

- Status: `done`
- Created: `2026-03-08`
- Last Updated: `2026-03-08`
- Related Backlog Item: `T-002`
- Related Modules: `AGENTS.md`, `docs/tasks/README.md`, `docs/system-checklist.md`

## Context

Current task-tracking rules are missing a clear distinction between partial-progress commits and closure commits, which can cause inconsistent backlog cleanup and process drift.

The project needs a lightweight solo-safe model that supports:

- frequent sync commits (for example when switching machines),
- explicit user-controlled task closure,
- consistent commit/backlog traceability.

## Scope

In scope:

- Define commit intent types: checkpoint vs closure.
- Define allowed task states for each commit type.
- Require explicit user instruction before setting `done`.
- Define backlog handling for open vs closed tasks.
- Define commit-message tagging and `T-###` reference requirements.

Out of scope:

- Git hooks or automation scripts.
- Branching strategy changes.

## Proposed Rules

1. Task IDs remain `T-###` and are managed from `Last Issued ID` in `docs/system-checklist.md`.
2. Standard active statuses: `todo`, `in_progress`, `blocked`.
3. `done` is a controlled transition state and may be set only on explicit user instruction.
4. Commit type tags are mandatory:
   - `[checkpoint]` for partial/in-progress synchronization commits.
   - `[close]` for closure commits.
5. `[checkpoint]` commits:
   - Allowed while task is `todo`, `in_progress`, or `blocked`.
   - Must reference relevant `T-###` IDs in commit body.
   - Must keep the task in active backlog.
6. `[close]` commits:
   - Require explicit user instruction to set task to `done` first.
   - Must reference relevant `T-###` IDs in commit body.
   - Must remove closed `T-###` item(s) from active backlog in the same commit.
7. Post-commit check:
   - Run `git status` and report residual changes, if any.

## Acceptance Criteria

- [x] `AGENTS.md` includes explicit policy for `[checkpoint]` and `[close]` usage.
- [x] `AGENTS.md` states that `done` transition requires explicit user instruction.
- [x] `docs/tasks/README.md` contains full lifecycle rules for backlog + commit types.
- [x] `docs/system-checklist.md` rules are aligned with the same logic.
- [x] Rule text unambiguously allows sync commits for non-done work.

## Implementation Notes

- Keep wording strict and auditable.
- Prefer short, imperative policy statements.
- Avoid duplicated contradictory rules across files.

## Validation Evidence

- Command(s) run:
  - `sed -n '1,220p' docs/system-checklist.md`
  - `ls -1 docs/tasks`
- Manual checks:
  - Confirmed new `T-002` row exists and links this file.
- Output summary:
  - Backlog updated and detailed task file created.

## Change Log

- `2026-03-08` - Initial draft.
- `2026-03-08` - Implemented rule updates across AGENTS and docs policy files.
- `2026-03-08` - Marked done on explicit user instruction.
