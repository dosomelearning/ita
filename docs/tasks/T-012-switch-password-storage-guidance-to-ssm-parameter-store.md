# T-012: Switch Password Storage Guidance to SSM Parameter Store

## Metadata

- Status: `done`
- Created: `2026-03-09`
- Last Updated: `2026-03-09`
- Related Backlog Item: `T-012`
- Related Modules: `AGENTS.md`, `README.md`, `b-ms1-ingress/README.md`, `b-ms4-statemgr/README.md`, `ARCHITECTURE.md`, `docs/system-checklist.md`

## Context

Current docs state that the shared class password is stored in DynamoDB. This creates ambiguity with service boundaries because DynamoDB is also part of `MS4` workflow/state responsibilities.

For the current scope, password storage is a single-secret/configuration concern and is better aligned with SSM Parameter Store.

## Scope

In scope:

- Replace documentation guidance from shared-password-in-DynamoDB to shared-password-in-SSM-Parameter-Store.
- Keep `MS4` DynamoDB usage focused on workflow state and aggregation.
- Add/adjust architecture decisions to reflect this storage split and rationale.

Out of scope:

- Runtime implementation of password retrieval/rotation.
- Deployment/runtime migration scripts.

## Acceptance Criteria

- [x] `T-012` backlog item added and set to `in_progress`.
- [x] Project docs no longer state that shared password is stored in DynamoDB as current behavior.
- [x] Project docs explicitly state shared password storage in SSM Parameter Store.
- [x] Architecture decision log includes this storage-boundary decision.
- [x] `MS4` state DynamoDB responsibility remains clear and separate.

## Implementation Notes

- Keep docs explicit that this is a current-phase architectural choice and can evolve later.
- Preserve service-boundary clarity: password/config storage (`MS1`) vs workflow state storage (`MS4`).

## Validation Evidence

- Command(s) run:
  - `rg -n "shared password|DynamoDB|Parameter Store|password" AGENTS.md README.md b-ms1-ingress/README.md b-ms4-statemgr/README.md docs/system-checklist.md docs/tasks`
  - `rg -n "shared password.*DynamoDB|password.*DynamoDB|stored in DynamoDB" AGENTS.md README.md b-ms1-ingress/README.md b-ms4-statemgr/README.md ARCHITECTURE.md docs/tasks/T-012-switch-password-storage-guidance-to-ssm-parameter-store.md`
- Manual checks:
  - Confirmed prior docs referenced DynamoDB for password storage.
  - Confirmed current architecture/docs state SSM Parameter Store for password and keep DynamoDB aligned with `MS4` state concerns.
- Output summary:
  - `T-012` opened and implemented for documentation and architecture-decision alignment.

## Change Log

- `2026-03-09` - Initial task file created.
- `2026-03-09` - Updated docs and ADs to use SSM Parameter Store for shared password; kept DynamoDB scope with `MS4` state.
- `2026-03-09` - Marked task as done and prepared closure commit.
