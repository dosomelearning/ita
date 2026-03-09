# T-008: Scaffold b-ms4-statemgr with AWS SAM

## Metadata

- Status: `done`
- Created: `2026-03-08`
- Last Updated: `2026-03-09`
- Related Backlog Item: `T-008`
- Related Modules: `b-ms4-statemgr`, `docs/system-checklist.md`

## Context

`b-ms4-statemgr` needs an initial AWS SAM scaffold so state and aggregation capabilities can be implemented with clear service ownership.

## Scope

In scope:

- Create/standardize baseline AWS SAM project structure for `b-ms4-statemgr`.
- Establish template skeleton, API/handler entry points, and baseline module layout.
- Document canonical module commands in `b-ms4-statemgr/README.md` once chosen.

Out of scope:

- Full state machine implementation.
- Final read API contract and ranking logic.
- End-to-end state synchronization behavior.

## Acceptance Criteria

- [x] `b-ms4-statemgr` has a baseline SAM scaffold suitable for iterative development.
- [x] `b-ms4-statemgr/README.md` documents canonical `install`/`test`/`lint`/`run` commands.
- [x] Scaffold preserves service ownership boundaries and avoids hidden coupling.

## Implementation Notes

- Keep scaffold minimal and reversible.
- Avoid embedding non-scaffold business logic.
- Keep API/state contract specifics for dedicated follow-up tasks.

## Validation Evidence

- Command(s) run:
  - `sed -n '1,220p' docs/system-checklist.md`
- Manual checks:
  - Confirmed `T-008` backlog item exists and links this task file.
- Output summary:
  - Backlog and detailed task entry created.

## Change Log

- `2026-03-08` - Initial draft.
