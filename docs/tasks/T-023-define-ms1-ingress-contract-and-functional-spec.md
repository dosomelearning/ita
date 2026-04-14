# T-023: Define MS1 Ingress Contract and Functional Specification

## Metadata

- Status: `in_progress`
- Created: `2026-04-14`
- Last Updated: `2026-04-14`
- Related Backlog Item: `T-023`
- Related Modules: `b-ms1-ingress/README.md`, `docs/tasks/T-010-define-frontend-backend-exchange-contracts.md`, `docs/system-checklist.md`

## Context

`MS4` contract and implementation baseline are now in place. Before implementing `MS1`, ingress behavior must be specified in concrete, testable terms: public upload-init API shape, password validation, presigned URL issuance, and mandatory synchronous init registration into `MS4`.

## Scope

In scope:

- Define `MS1` upload-init endpoint behavior and payload contracts.
- Define shared-password validation flow via SSM Parameter Store.
- Define presigned S3 upload target semantics and response payload.
- Define mandatory sync `MS1 -> MS4` init registration behavior.
- Define error semantics, idempotency, and observability baseline.

Out of scope:

- Full `MS1` implementation code.
- Full frontend integration with `MS1`.
- Queue payload schema details for downstream workers.

## AD Dependencies

- `AD-004` - Shared password admission check at `MS1` is mandatory before protected flow.
- `AD-005` - Public ingress API must be rate-limited.
- `AD-008` - `MS1` remains dedicated upload-init API surface (separate from `MS4` API).
- `AD-010` - Ingress is synchronous API mode and must align with async backend workflow start.
- `AD-011` - Password source is SSM Parameter Store (not DynamoDB).
- `AD-016` - `MS1` must synchronously register upload-init state in `MS4`.
- `AD-017` - Queue contracts are infra-owned; message emission is S3-event-driven after upload.

## Acceptance Criteria

- [ ] `MS1` endpoint contract (`POST /v1/uploads/init`) is explicitly documented.
- [ ] Password validation and reject behavior are documented.
- [ ] Presigned URL response contract and upload key strategy are documented.
- [ ] Sync failure behavior for `MS1 -> MS4` registration is documented.
- [ ] Standardized error envelope and status mapping are documented.

## Implementation Notes

Primary consistency rule: `MS1` success response is allowed only after both password validation and successful `MS4` init registration.

## Validation Evidence

- Command(s) run:
  - `cat b-ms1-ingress/README.md`
  - `cat docs/system-checklist.md`
  - `cat docs/tasks/T-010-define-frontend-backend-exchange-contracts.md`
- Manual checks:
  - Confirmed `MS4` contract baseline exists and is implementation-ready.
- Output summary:
  - Added dedicated `MS1` contract-first spec task and linked active backlog entry.

## Change Log

- `2026-04-14` - Initial draft.
