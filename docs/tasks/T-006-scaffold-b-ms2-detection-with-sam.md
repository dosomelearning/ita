# T-006: Scaffold b-ms2-detection with AWS SAM

## Metadata

- Status: `todo`
- Created: `2026-03-08`
- Last Updated: `2026-03-08`
- Related Backlog Item: `T-006`
- Related Modules: `b-ms2-detection`, `docs/system-checklist.md`

## Context

`b-ms2-detection` needs an initial AWS SAM scaffold so detection orchestration can be implemented in a controlled and testable sequence.

## Scope

In scope:

- Create/standardize baseline AWS SAM project structure for `b-ms2-detection`.
- Establish template skeleton, handler entry points, and baseline module layout.
- Document canonical module commands in `b-ms2-detection/README.md` once chosen.

Out of scope:

- Full Rekognition integration logic.
- Final queue message contract implementation.
- End-to-end detection-to-extraction integration.

## Acceptance Criteria

- [ ] `b-ms2-detection` has a baseline SAM scaffold suitable for iterative development.
- [ ] `b-ms2-detection/README.md` documents canonical `install`/`test`/`lint`/`run` commands.
- [ ] Scaffold aligns with queue-consumer role while preserving shared-resource ownership boundaries.

## Implementation Notes

- Keep scaffold minimal and reversible.
- Avoid embedding non-scaffold business logic.
- Keep message-contract specifics for dedicated follow-up tasks.

## Validation Evidence

- Command(s) run:
  - `sed -n '1,220p' docs/system-checklist.md`
- Manual checks:
  - Confirmed `T-006` backlog item exists and links this task file.
- Output summary:
  - Backlog and detailed task entry created.

## Change Log

- `2026-03-08` - Initial draft.
