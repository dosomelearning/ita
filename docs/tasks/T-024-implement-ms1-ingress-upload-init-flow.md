# T-024: Implement MS1 Ingress Upload-Init Flow

## Metadata

- Status: `in_progress`
- Created: `2026-04-14`
- Last Updated: `2026-04-14`
- Related Backlog Item: `T-024`
- Related Modules: `b-ms1-ingress/src/main.py`, `b-ms1-ingress/src/api.py`, `b-ms1-ingress/src/domain.py`, `b-ms1-ingress/src/service.py`, `b-ms1-ingress/src/ms4_client.py`, `b-ms1-ingress/template.yaml`, `b-ms1-ingress/tests/unit/test_domain.py`, `b-ms1-ingress/tests/unit/test_service.py`, `b-ms1-ingress/tests/unit/test_api.py`, `b-ms1-ingress/tests/unit/test_main.py`

## Context

`MS1` was scaffold-only. To unblock end-to-end ingress flow, `MS1` now needs concrete implementation for upload-init admission: validate shared password, issue presigned URL to shared processing bucket, and synchronously register initial upload state in `MS4`.

## Scope

In scope:

- Implement `POST /v1/uploads/init` in `MS1`.
- Validate password via SSM Parameter Store.
- Generate upload key and presigned `PUT` URL for shared processing bucket.
- Perform mandatory sync `MS1 -> MS4` init registration.
- Return standardized success/error payloads.
- Add unit tests for domain/service/api/handler layers.
- Update SAM template with API route, env vars, and required IAM policies.

Out of scope:

- `MS1` integration into SPA submit path.
- Full downstream worker contract validation (`MS2`/`MS3` runtime flow).
- Deployment execution by agent.

## AD Dependencies

- `AD-004` - Shared-password gate at ingress is mandatory.
- `AD-005` - Public ingress endpoint must be rate-limited.
- `AD-008` - `MS1` retains upload-init API ownership.
- `AD-010` - Sync API mode for ingress admission.
- `AD-011` - Password source is SSM Parameter Store.
- `AD-016` - Sync `MS1 -> MS4` init registration required before success response.
- `AD-017` - Queue handoff remains infra/S3-event-driven (not direct MS1 queue publish).

## Acceptance Criteria

- [x] `MS1` exposes `POST /v1/uploads/init`.
- [x] Invalid password requests are rejected and do not issue presigned URLs.
- [x] Accepted requests return upload target details (`uploadId`, presigned URL, key, headers).
- [x] `MS1` calls `MS4 /internal/uploads/init` and fails request if registration fails.
- [x] Unit tests cover domain/service/api/handler seams.
- [x] SAM template includes required API route and IAM permissions.

## Implementation Notes

- Code structure follows testable layering: `domain` -> `service` -> `api` -> `main`.
- `MS4` internal call is SigV4-signed (`execute-api`) using runtime credentials.
- Runtime avoids DynamoDB/queue writes in `MS1`; queue message emission is triggered by S3 upload events in shared infra.

## Validation Evidence

- Command(s) run:
  - `./b-ms1-ingress/scripts/run_tests.sh`
  - `cd b-ms1-ingress && sam validate --template-file template.yaml`
- Manual checks:
  - Reviewed error envelope consistency with project contract pattern.
  - Verified route and IAM/auth shape align with ingress responsibilities.
- Output summary:
  - Unit tests passed (`12` total).
  - SAM template validation passed.

## Change Log

- `2026-04-14` - Initial implementation and tests added.
