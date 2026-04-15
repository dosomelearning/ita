# T-017: Define Cross-Service Queue Contracts and DLQ Operations

## Metadata

- Status: `in_progress`
- Created: `2026-03-09`
- Last Updated: `2026-04-15`
- Related Backlog Item: `T-017`
- Related Modules: `b-infra/README.md`, `docs/tasks/T-003-setup-b-infra-shared-stack.md`, `b-ms2-detection/README.md`, `b-ms3-faces/README.md`, `docs/process/photo-upload-processing-sequence.md`

## Context

`T-003` established shared infra resources (queues, DLQs, and wiring), but detailed queue contract definitions are intentionally split into dedicated follow-up work.

## Scope

In scope:

- Define payload contract plan for cross-service boundary queues.
- Define contract versioning strategy.
- Define retry semantics and failure taxonomy alignment with queue/DLQ behavior.
- Define DLQ replay procedure and operational safety notes.

Out of scope:

- Major infrastructure re-architecture.
- Service implementation rewrites.

## Acceptance Criteria

- [x] Queue payload schema documentation plan exists for each boundary queue.
- [x] Versioning approach is documented.
- [x] Retry and error-handling semantics are documented.
- [x] DLQ replay procedure is documented with safety constraints.
- [x] Relevant module docs are updated/linked for discoverability.

## AD Dependencies

- `AD-003`: Async queue boundaries and DLQ handling are core to this task scope.
- `AD-017`: Queue/DLQ ownership is centralized in `b-infra`; this task defines contract/operations layer on top.
- `AD-020`: Alarm strategy depends on meaningful queue/DLQ semantics and replay procedures.

## Implementation Notes

- Keep resource ownership and contract ownership as separate concerns.
- Keep contract docs concise and operationally actionable.

### Queue Contracts (v1)

#### 1) Uploaded Photos Queue (`S3 uploaded/* -> MS2`)

Envelope strategy:

- Producer is S3 event notification.
- `MS2` consumes the AWS S3 event record envelope as-is.
- Contract versioning:
  - `contractVersion = s3-event-v1` (logical version label in `MS2` parser).
  - Backward compatibility policy: parser tolerates extra fields and ignores unknown keys.

Required payload fields for processing decision:

- `Records[].eventSource == "aws:s3"`
- `Records[].eventName` starts with `ObjectCreated`
- `Records[].s3.bucket.name`
- `Records[].s3.object.key`

Semantic rules:

- `s3.object.key` must be under `uploaded/` prefix; other prefixes are ignored (idempotent no-op).
- URL-decoded object key is canonicalized before downstream use.
- `uploadId` derivation is from key path segment after final `/` and before extension for current phase.

#### 2) Faces Extraction Queue (`MS2 -> MS3`)

Envelope strategy:

- Producer is `MS2`.
- Message body is JSON object (UTF-8).
- Contract versioning:
  - `contractVersion = "faces-extraction.v1"`.
  - Future non-breaking changes allowed by adding optional fields only.

Required body fields:

- `contractVersion` (`"faces-extraction.v1"`)
- `uploadId`
- `sessionId`
- `sourceBucket`
- `sourceKey`
- `detectionArtifactKey`
- `detectedFaces` (integer, `>= 0`)
- `eventTime` (ISO 8601 UTC)

Optional body fields:

- `nickname`
- `trace` object (`correlationId`, `requestId`, `producer`)

Semantic rules:

- `detectedFaces == 0` is valid and should still produce a message only if `MS3` needs explicit no-face closure behavior.
- For current rollout, `MS2` publishes extraction message only when `detectedFaces > 0`; otherwise `MS2` finalizes with failure/special status policy in `MS4` (to be aligned with `MS3` delivery phase).
- `sourceKey` in `faces-extraction.v1` should reference the relocated object under `processed/faces/*`, not the original ingress key under `uploaded/*`.

### Retry and Failure Taxonomy

Processing classification for `MS2`:

- Retriable (raise error, let Lambda/SQS retry):
  - Rekognition transient/service errors.
  - S3 transient errors.
  - `MS4` dependency unavailable (`5xx`/timeout).
  - SQS send failure to extraction queue.
- Non-retriable (ack message, emit `failed` state event where possible):
  - Malformed S3 event contract.
  - Unsupported key prefix/content.
  - Permanent validation errors (missing required metadata that cannot recover).

Retry behavior (infra-owned):

- Uploaded queue `maxReceiveCount = 5`, then DLQ.
- Faces extraction queue `maxReceiveCount = 5`, then DLQ.

Observability requirements:

- Log `uploadId`, source queue message ID, normalized object key, and failure class (`retriable`/`non_retriable`).
- Include `contractVersion` in producer/consumer logs.

### DLQ Replay Procedure (Safe Runbook v1)

Pre-checks:

1. Identify root cause category and ensure code/config fix is deployed first.
2. Estimate replay batch size and target window.
3. Confirm downstream dependencies (`MS4`, Rekognition, S3, queues) are healthy.

Replay safety rules:

1. Replay in bounded batches (for example 10-50 messages), not full-drain.
2. Preserve original message body; do not rewrite payload in replay path.
3. Ensure consumer idempotency semantics are active before replay.
4. Monitor queue age, DLQ growth, and API/Lambda errors during replay.
5. Stop replay immediately on repeated deterministic validation failures.

Post-checks:

1. Validate `MS4` state progression for sampled `uploadId`s.
2. Confirm no unexpected backlog growth in downstream queue.
3. Record replay window, count, and incident notes.

## Validation Evidence

- Command(s) run:
  - `cat b-infra/template-infra.yaml`
  - `cat docs/process/photo-upload-processing-sequence.md`
  - `cat b-ms4-statemgr/README.md`
  - `cat b-ms2-detection/README.md`
  - `cat b-ms3-faces/README.md`
- Manual checks:
  - Confirmed queue names, DLQ wiring, and retention/retry defaults from shared infra template.
  - Aligned contract flow with documented end-to-end sequence.
- Output summary:
  - Established `v1` queue contract definitions, versioning policy, retry taxonomy, and DLQ replay runbook.

## Change Log

- `2026-03-09` - Initial task file created as follow-up split from `T-003`.
- `2026-04-15` - Added concrete queue contracts (`s3-event-v1`, `faces-extraction.v1`), retry taxonomy, and DLQ replay safety runbook.
- `2026-04-15` - Linked contract definitions into `MS2`/`MS3` module READMEs for discoverability.
