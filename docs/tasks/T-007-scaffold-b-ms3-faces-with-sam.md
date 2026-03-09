# T-007: Scaffold b-ms3-faces with AWS SAM

## Metadata

- Status: `done`
- Created: `2026-03-08`
- Last Updated: `2026-03-09`
- Related Backlog Item: `T-007`
- Related Modules: `b-ms3-faces`, `docs/system-checklist.md`

## Context

`b-ms3-faces` needs an initial AWS SAM scaffold so face-extraction behavior can be implemented iteratively with clear module boundaries.

## Scope

In scope:

- Create/standardize baseline AWS SAM project structure for `b-ms3-faces`.
- Establish template skeleton, handler entry points, and baseline module layout.
- Document canonical module commands in `b-ms3-faces/README.md` once chosen.

Out of scope:

- Full face extraction implementation.
- Final artifact metadata model.
- End-to-end integration behavior across downstream state updates.

## Acceptance Criteria

- [x] `b-ms3-faces` has a baseline SAM scaffold suitable for iterative development.
- [x] `b-ms3-faces/README.md` documents canonical `install`/`test`/`lint`/`run` commands.
- [x] Scaffold aligns with queue-consumer role while preserving shared-resource ownership boundaries.

## Implementation Notes

- Keep scaffold minimal and reversible.
- Avoid embedding non-scaffold business logic.
- Keep extraction and artifact-policy specifics for dedicated follow-up tasks.

## Validation Evidence

- Command(s) run:
  - `sed -n '1,220p' docs/system-checklist.md`
- Manual checks:
  - Confirmed `T-007` backlog item exists and links this task file.
- Output summary:
  - Backlog and detailed task entry created.

## Change Log

- `2026-03-08` - Initial draft.
