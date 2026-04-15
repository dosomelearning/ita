# T-010: Define Frontend/Backend Exchange Contracts (MS1 + MS4)

## Metadata

- Status: `in_progress`
- Created: `2026-03-08`
- Last Updated: `2026-04-14`
- Related Backlog Item: `T-010`
- Related Modules: `f-spa`, `b-ms1-ingress`, `b-ms4-statemgr`, `docs/system-checklist.md`

## Context

The architecture has two frontend contact points:

- `MS1` (`b-ms1-ingress`) for presigned upload URL preparation.
- `MS4` (`b-ms4-statemgr`) for workflow state and result retrieval.

To avoid integration ambiguity, business-level communication patterns must be defined before detailed implementation.

## Scope

In scope:

- Define business-level request/response patterns between frontend and backend.
- Define frontend interactions with `MS1` for upload initialization and admission outcomes.
- Define frontend interactions with `MS4` for state polling/reading and result retrieval.
- Define business-level error categories and expected frontend behavior per category.
- Define correlation and state-tracking expectations across frontend-visible flows.

Out of scope:

- Detailed low-level payload schema for internal microservice-to-microservice messages.
- Full implementation of APIs.
- UI implementation specifics.

## AD Dependencies

- `AD-008` - Two API surfaces are preserved (`MS1` for upload-init, `MS4` for status/result read and state authority).
- `AD-010` - Contract supports synchronous API paths plus asynchronous backend update paths.
- `AD-011` - Password validation remains in `MS1` via SSM; `MS4` focuses on workflow state.
- `AD-016` - Upload-init registration from `MS1` to `MS4` is mandatory and synchronous.

## Acceptance Criteria

- [ ] A clear business interaction map exists for frontend <-> `MS1` and frontend <-> `MS4`.
- [ ] Required frontend request intents and backend response intents are documented.
- [ ] Error/edge scenarios are documented at business-contract level.
- [ ] Contract descriptions are consistent with async processing model and queue-based backend flow.
- [ ] Module READMEs are updated or linked so contract ownership is discoverable.

## Implementation Notes

- Keep contracts business-oriented first: what user flow step is requested and what outcome/status is returned.
- Keep `MS1` scope narrow: admission + presigned URL initiation only.
- Keep `MS4` scope explicit: workflow status/results read model for frontend.
- Ensure terms are consistent across root and module documentation.

## Contract Draft (Current Working Specification)

### 1) MS4 Capability Boundaries

`MS4` is the authoritative workflow state service. It does not issue presigned URLs and does not run face detection/extraction logic.

`MS4` responsibilities:

- Persist workflow lifecycle state per `uploadId`.
- Accept state mutation calls from trusted backend services (`MS1`, `MS2`, `MS3`).
- Expose frontend-readable state/result contract for polling.
- Provide frontend-readable class activity feed projection.

### 2) Canonical State Model

Canonical states for frontend and service contracts:

- `queued` - request accepted and registered; processing not yet started.
- `processing` - one or more backend stages are active or partially complete.
- `completed` - processing finished with available results.
- `failed` - processing cannot continue without retry/new submission.

State ownership and transition intent:

- `MS1` creates initial record as `queued`.
- `MS2` can transition `queued -> processing` (or `queued/processing -> failed`).
- `MS3` can transition `processing -> completed` (or `processing -> failed`).
- `MS4` rejects invalid backward transitions (for example `completed -> processing`).

### 3) API Surface (Business-Level)

`MS1 -> MS4` (sync, required):

- `POST /internal/uploads/init`
- Intent: register upload-init state before `MS1` responds success to SPA.
- Success outcome: upload record exists in `queued`.

`MS2/MS3 -> MS4` (sync or async-triggered HTTP write, service-authenticated):

- `POST /internal/uploads/{uploadId}/events`
- Intent: append stage event and update derived current state.
- Success outcome: event recorded; state projection updated idempotently.

`SPA -> MS4` (frontend read):

- `GET /v1/uploads/{uploadId}/status`
- Intent: retrieve current state and result references for rendering.
- Success outcome: returns one of `queued|processing|completed|failed` plus metadata.

Activity feed extension (current direction):

- `GET /v1/sessions/{sessionId}/activities`
- Intent: fetch latest session activities (event-level feed), newest first.
- Default limit: `20` (bounded).

### 3.1) Internal API Authentication Decision

Decision (accepted for current implementation phase):

- All `MS4` internal write endpoints under `/internal/*` use API Gateway auth type `AWS_IAM`.
- Internal endpoints are not intended for public SPA usage.
- Service-to-service callers (`MS1`, `MS2`, `MS3`) invoke using IAM-signed requests with least-privilege `execute-api:Invoke` permissions scoped to required methods/routes only.
- Deny-by-default posture is required; avoid wildcard invoke grants.

Implications:

- No shared static service secret is introduced for internal service auth.
- Caller principal context should be logged by `MS4` for auditability.

### 3.2) API Gateway Route Mapping Decision

Decision (accepted for current implementation phase):

- `MS4` uses one API Gateway with path-based contract separation.
- Internal service routes:
  - `/internal/*`
  - Auth: `AWS_IAM`
  - Intended callers: `MS1`, `MS2`, `MS3`
- Frontend routes:
  - `/v1/*`
  - Intended caller: SPA
  - Enforce public endpoint throttling/rate limits per project constraints.

Initial route set:

- `POST /internal/uploads/init`
- `POST /internal/uploads/{uploadId}/events`
- `GET /v1/uploads/{uploadId}/status`
- `GET /v1/sessions/{sessionId}/participants/{nickname}/uploads`

Implementation guardrail:

- Keep internal and frontend route handling separated to avoid auth or validation policy leakage across route classes.

### 4) Minimal Payload Contract (Business Fields)

Upload-init write (`POST /internal/uploads/init`) required fields:

- `uploadId` (string, globally unique within environment)
- `sessionId` (string, class run/session correlation)
- `nickname` (participant display name; normalized by MS4 for participant history keying)
- `submittedAt` (ISO 8601 timestamp)
- `source` (enum-like string; currently `spa`)

Processing event write (`POST /internal/uploads/{uploadId}/events`) required fields:

- `eventType` (for example `detection_started`, `detection_completed`, `extraction_completed`, `processing_failed`)
- `eventTime` (ISO 8601 timestamp)
- `producer` (`ms2` or `ms3`)
- `statusAfter` (`processing|completed|failed`)
- `details` (object, optional stage metadata such as counts/reason codes/result refs)

Frontend status read (`GET /v1/uploads/{uploadId}/status`) response fields:

- `uploadId`
- `status` (`queued|processing|completed|failed`)
- `updatedAt`
- `progress` (optional object with stage hints)
- `results` (optional object; for `completed`, includes face artifact refs/metadata)
- `error` (optional object; for `failed`, includes user-safe reason and retry hint)

Frontend participant history read (`GET /v1/sessions/{sessionId}/participants/{nickname}/uploads`) response fields:

- `sessionId`
- `nickname`
- `participantId` (normalized identity key)
- `items` (status-read projection list, newest first)

Frontend activity feed read (`GET /v1/sessions/{sessionId}/activities`) response fields:

- `sessionId`
- `items` (event feed entries, newest first)
- Feed item fields:
  - `uploadId`
  - `nickname`
  - `participantId`
  - `eventType`
  - `statusAfter`
  - `eventTime`
  - `producer`
  - `outcome` (`queued|in_progress|success|failure`)
  - `details` (optional stage metadata)

### 4.1) Result Reference Format Decision

Decision (accepted for current implementation phase):

- `MS4` returns CloudFront HTTPS URLs for frontend-consumable result artifacts.
- `MS4` stores canonical object identity internally as S3 data (`bucket`, `key`, optional `versionId`) in DynamoDB.
- Frontend-facing contract should avoid raw `s3://...` URIs in normal paths.

Contract direction:

- `results.faces[].url` contains CloudFront URL for SPA rendering.
- Internal S3 key data remains available for backend operations/debug paths as needed, but is not required for standard SPA contract.

### 5) Idempotency and Ordering Rules

- `uploadId` is the idempotency key for init registration; repeated init calls with same semantic payload are no-op success.
- Stage events must carry deterministic dedupe key semantics (`uploadId + eventType + producer + eventTime` or explicit event ID).
- Out-of-order events are tolerated:
  - Events are stored for audit.
  - Derived state is computed with transition guardrails (no illegal backward state).
- `completed` and terminal `failed` are treated as terminal unless explicit replay policy is later documented.

### 6) Error Categories and HTTP Semantics

- `400` - contract violation (missing/invalid fields).
- `404` - unknown `uploadId` for event/status paths.
- `409` - rejected transition or conflicting terminal state mutation.
- `429` - throttled (API Gateway/usage plan policy).
- `5xx` - service-side failure; client or producer should retry according to caller policy.

Frontend behavior mapping:

- `queued|processing` -> continue polling.
- `completed` -> render results.
- `failed` -> render retry/new-upload guidance.
- `404` on status shortly after init may be treated as transient for short bounded retry window.

### 6.1) Standard Error Payload Decision

Decision (accepted for current implementation phase):

- `MS4` uses one JSON error envelope format across internal and frontend routes.

Payload shape:

- `error.code` (stable machine-readable error code)
- `error.message` (human-readable, user-safe on frontend routes)
- `error.retryable` (boolean)
- `error.details` (optional object; non-sensitive diagnostics)
- `requestId`
- `timestamp` (ISO 8601)

Status-to-code mapping baseline:

- `400` -> `VALIDATION_ERROR`
- `404` -> `UPLOAD_NOT_FOUND`
- `409` -> `INVALID_TRANSITION` or `TERMINAL_STATE_CONFLICT`
- `429` -> `THROTTLED`
- `500` -> `INTERNAL_ERROR`
- `503` -> `DEPENDENCY_UNAVAILABLE` (when applicable)

Contract rules:

- `message` on `/v1/*` must remain user-safe and non-sensitive.
- `details` may be richer on `/internal/*`, but must not include secrets.
- `retryable` must be set consistently to drive caller retry behavior.

### 7) MS4 Required Infra Inputs

From `ita-infra` outputs (already available):

- `SharedProcessingBucketName` (for resolving artifact references)
- `UploadedPhotosQueueArn/Url` and `FacesExtractionQueueArn/Url` (indirect pipeline context)
- `SystemAlarmsTopicArn` (observability integration)

Service-owned in `b-ms4-statemgr` stack:

- API/Lambda resources.
- State table(s) for projection/event data.

### 7.1) DynamoDB Data Model Decision

Decision (accepted for current implementation phase):

- `MS4` uses a single DynamoDB table with `uploadId`-centered partitioning.
- Primary key structure:
  - `PK = UPLOAD#<uploadId>`
  - `SK = STATE` for current projection item
  - `SK = EVENT#<eventTime>#<eventType>#<producer>` for immutable event log items
- `STATE` item carries current status/read projection fields.
- `EVENT` items carry append-only audit/event history.
- `GSI3` supports session activity feed query:
  - `gsi3pk = FEED#CLASS#<classRunId>`
  - `gsi3sk = E#<eventTimeMs>#U#<uploadId>#T#<eventType>`
  - Query: `ScanIndexForward=false`, `Limit=20` (or caller-provided bounded limit).

Access-pattern guardrail (mandatory):

- DynamoDB `Scan` is not allowed for `MS4` runtime paths.
- Retrieval must use only `GetItem` and `Query` APIs (including GSI queries where needed).
- Data model and indexes must be designed around known query patterns; no fallback scans.

### 8) Observability Requirements

Per-request/event logs should include:

- `uploadId`
- `sessionId` (if present)
- `producer` / API caller context
- previous and next state
- transition decision (applied/rejected)
- correlation/request ID

## Validation Evidence

- Command(s) run:
  - `sed -n '1,260p' docs/system-checklist.md`
  - `cat b-ms4-statemgr/README.md`
- Manual checks:
  - Confirmed `T-010` backlog item exists and status is now `in_progress`.
  - Verified spec aligns with architecture decisions and process sequence.
- Output summary:
  - Added contract-first `MS4` functionality specification and business-level API/state rules.
  - `MS1` implementation-ready contract details are tracked in `T-023`.

## Change Log

- `2026-03-08` - Initial draft.
- `2026-04-14` - Expanded into concrete MS4-first contract specification and moved task to `in_progress`.
