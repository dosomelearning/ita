# b-ms4-statemgr

State and aggregation microservice.

## Related Docs

- [`../README.md`](../README.md) (project overview and boundaries)
- [`../AGENTS.md`](../AGENTS.md) (project workflow and guardrails)
- [`../b-infra/README.md`](../b-infra/README.md)
- [`../b-ms1-ingress/README.md`](../b-ms1-ingress/README.md)
- [`../b-ms2-detection/README.md`](../b-ms2-detection/README.md)
- [`../b-ms3-faces/README.md`](../b-ms3-faces/README.md)
- [`../f-spa/README.md`](../f-spa/README.md)
- [`../docs/tasks/T-010-define-frontend-backend-exchange-contracts.md`](../docs/tasks/T-010-define-frontend-backend-exchange-contracts.md) (contract-first MS1/MS4 exchange specification)

## Purpose

`b-ms4-statemgr` maintains workflow state for upload, detection, and extraction and exposes frontend-facing state/result APIs.

## Ownership Model

- This microservice owns its own SAM template and service resources.
- Shared foundational resources are consumed from `b-infra` outputs.

## Responsibilities

- Define and expose state API endpoint(s) in this service template.
- Maintain processing state in DynamoDB.
- Serve frontend-readable references/URLs/metadata for completed jobs.
- Accept and apply status updates from upstream processing stages.
- Provide data foundations for class-oriented ranking/leaderboard views.

## Functional Specification (Pre-Implementation)

The sections below define the implementation target for the first MS4 delivery slice.

### API Endpoints (Initial)

- Internal init registration (from `MS1`):
  - `POST /internal/uploads/init`
  - Purpose: create initial upload state record as `queued`.
  - Requirement: synchronous and required before `MS1` returns success to SPA.
- Internal processing event write (from `MS2`/`MS3`):
  - `POST /internal/uploads/{uploadId}/events`
  - Purpose: append stage event and update derived current state.
- Frontend status read:
  - `GET /v1/uploads/{uploadId}/status`
  - Purpose: polling/read model for SPA async workflow UI.

### Internal API Authentication

- All routes under `/internal/*` use API Gateway authorization type `AWS_IAM`.
- Internal routes are intended only for trusted service callers (`MS1`, `MS2`, `MS3`), not direct SPA access.
- Caller stacks must grant least-privilege `execute-api:Invoke` permissions scoped to exact required methods/routes.
- Use deny-by-default IAM policy posture (no broad wildcard invoke grants).
- `MS4` should log caller principal context for traceability/audit.

### API Gateway Route Mapping

- Use one API Gateway for `MS4` with path-based separation:
  - `/internal/*` for service-to-service write paths (`AWS_IAM`).
  - `/v1/*` for frontend read paths (public, rate-limited).
- Initial route set:
  - `POST /internal/uploads/init`
  - `POST /internal/uploads/{uploadId}/events`
  - `GET /v1/uploads/{uploadId}/status`
- Keep internal and frontend route handlers logically separated to prevent policy leakage.

### Canonical State Machine

Supported states:

- `queued`
- `processing`
- `completed`
- `failed`

Allowed transition intent:

- init: `queued` (created by `MS1`)
- detection/extraction in progress: `queued -> processing`
- successful finish: `processing -> completed`
- failure: `queued|processing -> failed`

Guardrails:

- Reject backward transitions (for example `completed -> processing`).
- Treat `completed` and terminal `failed` as terminal in current phase.
- Keep an event history for audit even when transition is rejected.

### Contract Fields (Business-Level)

Init write required fields:

- `uploadId`
- `sessionId`
- `submittedAt` (ISO 8601)
- `source` (`spa`)

Event write required fields:

- `eventType`
- `eventTime` (ISO 8601)
- `producer` (`ms2` or `ms3`)
- `statusAfter`
- `details` (optional object)

Status read response fields:

- `uploadId`
- `status`
- `updatedAt`
- `progress` (optional)
- `results` (optional; populated for `completed`)
- `error` (optional; populated for `failed`)

### Result Reference Format

- Frontend-facing result references use CloudFront HTTPS URLs.
- Canonical artifact identity is stored internally as S3 object data (`bucket`, `key`, optional `versionId`).
- Raw `s3://` URIs are not part of normal SPA response contract.

### Idempotency and Ordering

- `uploadId` is idempotency key for init registration.
- Event ingestion must support idempotent replay and duplicate suppression.
- Out-of-order events are tolerated via transition guardrails and audit logging.

### Error Semantics

- `400` invalid/missing payload fields.
- `404` unknown upload for event/status query.
- `409` invalid transition or terminal-state conflict.
- `429` throttled request.
- `5xx` internal service failure; caller may retry based on caller policy.

### Standard Error Payload

All API errors should follow one JSON envelope:

- `error.code`
- `error.message`
- `error.retryable`
- `error.details` (optional, non-sensitive)
- `requestId`
- `timestamp` (ISO 8601)

Baseline status-to-code mapping:

- `400` -> `VALIDATION_ERROR`
- `404` -> `UPLOAD_NOT_FOUND`
- `409` -> `INVALID_TRANSITION` or `TERMINAL_STATE_CONFLICT`
- `429` -> `THROTTLED`
- `500` -> `INTERNAL_ERROR`
- `503` -> `DEPENDENCY_UNAVAILABLE` (when applicable)

Rules:

- Keep `/v1/*` error messages user-safe.
- Allow richer diagnostics in `/internal/*` `details` without exposing secrets.
- Set `retryable` consistently to support caller retry behavior.

### Required Infra Inputs

`MS4` depends on outputs from `ita-infra`:

- `SharedProcessingBucketName`
- `UploadedPhotosQueueArn/Url`
- `FacesExtractionQueueArn/Url`
- `SystemAlarmsTopicArn`

### DynamoDB Model and Access Rule

Current implementation direction:

- Single-table design centered on `uploadId`.
- `PK = UPLOAD#<uploadId>`.
- `SK = STATE` for current read projection.
- `SK = EVENT#<eventTime>#<eventType>#<producer>` for immutable event history.

Mandatory runtime access constraint:

- DynamoDB `Scan` is not allowed.
- Retrieval paths must use only `GetItem` and `Query` operations.
- Any new read requirement must be satisfied by key/index design, not table scans.

### Observability Baseline

Each write/read path should log:

- `uploadId`
- `sessionId` (if present)
- caller/producer identity
- prior and next state
- transition apply/reject decision
- correlation/request ID

## Inbound / Outbound Contracts

- Inbound:
  - API requests from frontend for state/result reads.
  - Status updates from `b-ms2-detection` and `b-ms3-faces`.
  - Optional upload-registration signal from `b-ms1-ingress`.
- Outbound:
  - API responses containing processing status and artifact references.

## Non-Functional Requirements

- API Gateway rate limiting is mandatory.
- State transitions must be explicit and auditable.
- Read model should tolerate eventual consistency in async workflow stages.

## Commands

- Install: `conda run -n conda_py_env_312 python -m pip install -r src/requirements.txt -r tests/requirements.txt`
- Test: `./scripts/run_tests.sh`
- Lint: `conda run -n conda_py_env_312 python -m ruff check src tests`
- Run: `sam build --template-file template.yaml`

## Open Decisions

- Leaderboard aggregation model and refresh strategy.
- State table ownership split (service-owned by MS4 vs explicitly shared table in `b-infra`).
