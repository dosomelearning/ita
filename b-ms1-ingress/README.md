# b-ms1-ingress

Ingress microservice for request admission and upload URL issuance.

## Related Docs

- [`../README.md`](../README.md) (project overview and boundaries)
- [`../AGENTS.md`](../AGENTS.md) (project workflow and guardrails)
- [`../b-infra/README.md`](../b-infra/README.md)
- [`../b-ms2-detection/README.md`](../b-ms2-detection/README.md)
- [`../b-ms3-faces/README.md`](../b-ms3-faces/README.md)
- [`../b-ms4-statemgr/README.md`](../b-ms4-statemgr/README.md)
- [`../f-spa/README.md`](../f-spa/README.md)

## Purpose

`b-ms1-ingress` is the entry point for upload initiation. It validates the shared one-time password and returns a presigned upload URL only for valid requests.

## Ownership Model

- This microservice owns its own SAM template and service resources.
- Shared foundational resources are consumed from `b-infra` outputs.

## Responsibilities

- Define and expose upload-init API endpoint(s) in this service template.
- Validate instructor-defined shared password (stored in SSM Parameter Store).
- Reject invalid password requests before protected flow.
- Generate and return S3 presigned URL + upload metadata for accepted requests.
- Register initial upload state with state manager (or via agreed event/API contract).
- Emit structured logs and metrics for admission outcomes.

## Functional Specification (Pre-Implementation)

The sections below define the first implementation target for `MS1`.

### API Endpoint (Initial)

- Frontend upload-init endpoint:
  - `POST /v1/uploads/init`
  - Purpose: password-gated admission and upload target issuance.
  - Caller: SPA.
  - Rate-limited at API Gateway (mandatory).

### Request Contract (Business-Level)

Required fields:

- `password` (shared class password)
- `nickname` (frontend user nickname for session context)
- `sessionId` (class/session correlation identifier)
- `contentType` (image media type, for example `image/jpeg`)

Optional fields:

- `originalFilename`
- `fileSizeBytes`

Validation baseline:

- `password`, `nickname`, `sessionId`, `contentType` must be non-empty strings.
- `password` must not contain whitespace (letters/numbers/special characters are allowed).
- `nickname` must start with a letter, contain only letters/numbers, and be max 20 characters (no spaces).
- Reject unsupported content types with explicit validation error.

Class-run grouping note:

- `MS1` derives canonical `classRunId` from validated class code and uses it for backend grouping (`MS4` session id + S3 key path).
- Raw class code is not propagated as runtime grouping identifier.

### Admission and Password Validation

- Password source is SSM Parameter Store (configured by env var parameter name).
- `MS1` reads configured shared password and performs constant-time compare with request password.
- Invalid password handling:
  - No presigned URL generation.
  - No `MS4` init call.
  - Return explicit auth failure response.

### Upload Target and Presigned URL

On successful admission:

- Generate `uploadId` in `MS1`.
- Build canonical object key under shared processing bucket:
  - Prefix: `uploaded/`
  - Include derived `classRunId` and `uploadId` in key path.
- Generate presigned `PUT` URL with bounded expiry.
- Include required upload headers in response (`Content-Type` and any required metadata headers).

Note:

- Queue message is not emitted by `MS1` directly.
- Downstream message to uploaded queue is produced by S3 event configuration after successful object upload.

### Mandatory Sync Registration in MS4

Before returning success to SPA, `MS1` must call:

- `POST /internal/uploads/init` on `MS4` (AWS_IAM-authenticated internal call).

Init payload baseline:

- `uploadId`
- `sessionId` (set to derived `classRunId`)
- `submittedAt` (ISO 8601)
- `source` (`spa`)
- `nickname` (forwarded as optional metadata field)

Consistency rule:

- If `MS4` init registration fails, `MS1` must fail the request (retriable error), and must not return a success upload-init response.
- After init registration, `MS1` records ordered sequence events in `MS4`:
  - `upload_init_received` (`producer=ms1`, `statusAfter=queued`, `details.phase=pending_upload`)
  - `upload_url_issued` (`producer=ms1`, `statusAfter=queued`, `details.phase=upload_ready`)

### Success Response Contract

Response baseline fields:

- `accepted: true`
- `uploadId`
- `classRunId`
- `uploadUrl` (presigned URL)
- `uploadMethod` (`PUT`)
- `uploadHeaders` (required request headers)
- `objectKey`
- `expiresInSeconds`

### Error Semantics and Envelope

Use standardized envelope shape:

- `error.code`
- `error.message`
- `error.retryable`
- `error.details` (optional, non-sensitive)
- `requestId`
- `timestamp`

Status-to-code baseline:

- `400` -> `VALIDATION_ERROR`
- `401` or `403` -> `INVALID_PASSWORD`
- `429` -> `THROTTLED`
- `503` -> `DEPENDENCY_UNAVAILABLE` (for `MS4`/SSM transient failures)
- `500` -> `INTERNAL_ERROR`

Rules:

- Never log plaintext password.
- Keep frontend-facing error messages user-safe and actionable.

### Idempotency and Retry Guidance

- Default behavior: each accepted call creates a new `uploadId`.
- Client retries after uncertain failures are allowed and may create new uploads unless client-supplied idempotency is introduced later.
- If `MS4` registration fails, response must be retryable and no successful init outcome should be emitted.

### Required Infra Inputs

From shared infra outputs/config:

- `SharedProcessingBucketName`
- Region and signing context for presign generation

From service config:

- `SharedPasswordSsmParameterName`
- `MS4InternalApiBaseUrl`

### Observability Baseline

Log fields per request:

- `requestId`
- `uploadId` (once generated)
- `sessionId`
- `nickname` (if policy permits; otherwise hashed/pseudonymized)
- admission decision (`accepted` / `rejected`)
- rejection reason code
- `MS4` registration outcome
- presign generation outcome

## Inbound / Outbound Contracts

- Inbound:
  - API Gateway request from frontend with shared password and upload context.
- Outbound:
  - Presigned URL response to frontend.
  - Optional registration event/state update to `b-ms4-statemgr`.
  - Upload target points to shared "uploaded photos" S3 bucket.

## Non-Functional Requirements

- API Gateway rate limiting is mandatory.
- Public route `POST /v1/uploads/init` is throttled at API Gateway stage route settings.
- Validation failure paths must be explicit and auditable.
- Keep credentials out of repo; use AWS profile-based auth for local tooling.

## Mandatory Runtime Rule

- Initialize AWS SDK clients in module-global scope.
- Do not initialize AWS SDK clients inside Lambda handler code paths.

## Commands

- Install: `conda run -n conda_py_env_312 python -m pip install -r src/requirements.txt -r tests/requirements.txt`
- Test: `./scripts/run_tests.sh`
- Lint: `conda run -n conda_py_env_312 python -m ruff check src tests`
- Run: `sam build --template-file template.yaml`

## Deployment Parameters

`MS1` template parameters are configured in `b-ms1-ingress/samconfig.toml` under:

- `[default.deploy.parameters].parameter_overrides`

Current overrides include:

- `ProcessingBucketName`
- `SharedPasswordSsmParameterName`
- `Ms4InternalApiBaseUrl`
- `PresignExpiresSeconds`
- `PublicInitThrottleRateLimit`
- `PublicInitThrottleBurstLimit`

## Open Decisions

- Password rotation/update workflow and class-session lifecycle governance.
- Correlation ID format shared across downstream services.
- Client-side idempotency key introduction strategy for duplicate-submit control.
