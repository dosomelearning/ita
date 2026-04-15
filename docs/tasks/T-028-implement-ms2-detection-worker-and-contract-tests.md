# T-028: Implement MS2 Detection Worker and Contract Tests

## Metadata

- Status: `done`
- Created: `2026-04-15`
- Last Updated: `2026-04-15`
- Related Backlog Item: `T-028`
- Related Modules: `b-ms2-detection/src/main.py`, `b-ms2-detection/src/api.py`, `b-ms2-detection/src/domain.py`, `b-ms2-detection/src/service.py`, `b-ms2-detection/src/ms4_client.py`, `b-ms2-detection/src/requirements.txt`, `b-ms2-detection/template.yaml`, `b-ms2-detection/tests/unit/test_domain.py`, `b-ms2-detection/tests/unit/test_service.py`, `b-ms2-detection/tests/unit/test_api.py`, `b-ms2-detection/tests/unit/test_main.py`, `scripts/test_local.sh`, `docs/testing/README.md`

## Context

`MS1`, `MS4`, and SPA wiring are implemented and validated. `MS2` is currently scaffold-only, so runtime flow remains stuck before detection/extraction progress is visible to frontend polling. `MS2` must now become the first asynchronous processing stage.

## Scope

In scope:

- Implement queue-driven `MS2` Lambda worker for uploaded-photo events.
- Parse/validate uploaded queue message contract (`s3-event-v1` from `T-017`).
- Run Rekognition face detection on uploaded objects.
- Persist detection artifact JSON to shared processing bucket.
- Emit processing event updates to `MS4` internal events endpoint.
- Publish extraction jobs to faces extraction queue (`faces-extraction.v1`).
- Add relevant unit tests across domain/service/api/handler seams.
- Update SAM template/IAM/env configuration for runtime dependencies.

Out of scope:

- `MS3` extraction implementation.
- New frontend feature work beyond observing status progression from `MS2`.
- Deployment execution by agent.

## AD Dependencies

- `AD-003` - Queue-based async boundary is the core processing model.
- `AD-010` - `MS2` is an async Lambda execution mode service.
- `AD-012` - Rekognition detection responsibility is owned by `MS2`.
- `AD-016` - `MS4` remains authoritative state projection endpoint.
- `AD-017` - Shared queues are infra-owned and consumed by service stack.

## Acceptance Criteria

- [x] `MS2` consumes uploaded queue events and validates required message fields.
- [x] `MS2` writes detection artifact(s) to shared processing bucket.
- [x] `MS2` posts `processing`/failure state events to `MS4` with standardized fields.
- [x] `MS2` emits `faces-extraction.v1` messages to faces extraction queue when faces are detected.
- [x] Unit tests cover parser/validation logic and success/failure branch behavior.
- [x] `b-ms2-detection/template.yaml` includes event source mapping, env vars, and least-privilege IAM permissions.

## Implementation Notes

- Follow established module pattern used by `MS1` and `MS4`: `domain` -> `service` -> `api` -> `main`.
- Keep retriable vs non-retriable error classification explicit in code and logs.
- Preserve idempotent-safe behavior for duplicate SQS deliveries.

## Validation Evidence

- Command(s) run:
  - `./scripts/run_tests.sh` (from `b-ms2-detection/`)
  - `./scripts/test_all.sh`
  - `./scripts/test_all.sh` (rerun with network-enabled execution for live checks)
- Manual checks:
  - Confirmed queue-contract docs and MS2/MS3 README contract linkage before implementation.
  - Runtime `MS4` transition observation from deployed `MS2` remains pending until deployment.
- Output summary:
  - Added contract-first `MS2` worker implementation and unit tests (`14` passing tests).
  - Updated centralized local test runner to include `MS2` unit tests.
  - Full cumulative suite passed in network-enabled run.

## Change Log

- `2026-04-15` - Initial task file created for `MS2` implementation and test coverage.
- `2026-04-15` - Implemented `MS2` worker/service/tests/template and integrated `MS2` into centralized local test tier.
