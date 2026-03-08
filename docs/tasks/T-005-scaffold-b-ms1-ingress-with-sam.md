# T-005: Scaffold b-ms1-ingress with AWS SAM

## Metadata

- Status: `todo`
- Created: `2026-03-08`
- Last Updated: `2026-03-08`
- Related Backlog Item: `T-005`
- Related Modules: `b-ms1-ingress`, `docs/system-checklist.md`

## Context

`b-ms1-ingress` needs an initial AWS SAM scaffold so ingress-specific functionality can be implemented incrementally on a stable module baseline.

## Scope

In scope:

- Create/standardize baseline AWS SAM project structure for `b-ms1-ingress`.
- Establish module-level entry points, template skeleton, and basic folder layout.
- Document canonical module commands in `b-ms1-ingress/README.md` once chosen.

Out of scope:

- Full shared-password validation implementation.
- Full presigned URL workflow implementation.
- Production-grade API contract finalization.

## Acceptance Criteria

- [ ] `b-ms1-ingress` has a baseline SAM scaffold suitable for iterative development.
- [ ] `b-ms1-ingress/README.md` documents canonical `install`/`test`/`lint`/`run` commands.
- [ ] Scaffold preserves service ownership boundaries and consumes shared infra via outputs/contracts.

## Implementation Notes

- Keep scaffold minimal and reversible.
- Avoid embedding non-scaffold business logic.
- Keep cross-service contracts explicit and deferred to dedicated tasks.

## Validation Evidence

- Command(s) run:
  - `sed -n '1,220p' docs/system-checklist.md`
- Manual checks:
  - Confirmed `T-005` backlog item exists and links this task file.
- Output summary:
  - Backlog and detailed task entry created.

## Change Log

- `2026-03-08` - Initial draft.
