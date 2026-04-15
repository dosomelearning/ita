# b-ms2-detection

Detection microservice for face detection orchestration.

## Related Docs

- [`../README.md`](../README.md) (project overview and boundaries)
- [`../AGENTS.md`](../AGENTS.md) (project workflow and guardrails)
- [`../b-infra/README.md`](../b-infra/README.md)
- [`../b-ms1-ingress/README.md`](../b-ms1-ingress/README.md)
- [`../b-ms3-faces/README.md`](../b-ms3-faces/README.md)
- [`../b-ms4-statemgr/README.md`](../b-ms4-statemgr/README.md)
- [`../f-spa/README.md`](../f-spa/README.md)

## Purpose

`b-ms2-detection` consumes uploaded-photo notifications, runs face detection with Rekognition, and publishes extraction-ready artifacts/events for downstream processing.

## Ownership Model

- This microservice owns its own SAM template and service resources.
- Shared foundational resources are consumed from `b-infra` outputs.

## Responsibilities

- Consume uploaded-photo events from SQS queue (fed by S3 notifications).
- Handle queue retry and DLQ behavior for failed processing attempts.
- Invoke Amazon Rekognition face detection.
- Persist detection artifacts/metadata (for example manifest) to shared storage.
- Publish face-extraction work items for `b-ms3-faces`.
- Report detection lifecycle status (`started`, `completed`, `failed`) to state manager.

## Inbound / Outbound Contracts

- Inbound:
  - SQS message from uploaded-photos notification queue.
- Outbound:
  - Rekognition artifacts and manifest records.
  - SQS message to faces-extraction queue.
  - Status updates routed to `b-ms4-statemgr`.

## Queue Contract (Current v1 Spec)

### Inbound: Uploaded Photos Queue (`s3-event-v1`)

`MS2` consumes the S3 event envelope received through SQS.

Required fields per record:

- `eventSource == "aws:s3"`
- `eventName` prefix `ObjectCreated`
- `s3.bucket.name`
- `s3.object.key`

Rules:

- `s3.object.key` must match `uploaded/*`; non-matching records are ignored as no-op.
- URL-decoded key is canonical processing key.
- Parser tolerates unknown fields for forward compatibility.
- After detection, `MS2` moves source object from `uploaded/` to:
  - `processed/faces/{sessionId}/{uploadId}.<ext>` when detected faces > 0
  - `processed/nofaces/{sessionId}/{uploadId}.<ext>` when detected faces = 0
- Downstream references (`MS4` details + faces-extraction queue payload) must use moved `processed/*` key, not original `uploaded/*` key.

### Outbound: Faces Extraction Queue (`faces-extraction.v1`)

`MS2` publishes JSON message body to the faces extraction queue.

Required fields:

- `contractVersion` (`faces-extraction.v1`)
- `uploadId`
- `sessionId`
- `sourceBucket`
- `sourceKey`
- `detectionArtifactKey`
- `detectedFaces`
- `eventTime` (ISO 8601 UTC)

Optional fields:

- `nickname`
- `trace` (`correlationId`, `requestId`, `producer`)

Emission rule:

- `MS2` publishes extraction job only when at least one face is detected.

## MS4 Event Contract Usage

`MS2` writes to `POST /internal/uploads/{uploadId}/events` with producer `ms2`.

Expected event progression:

- `upload_succeeded` -> `statusAfter: queued` (uses original S3 notification `eventTime`)
- `detection_started` -> `statusAfter: processing`
- `detection_completed` -> `statusAfter: processing`
- `detection_failed` -> `statusAfter: failed`

`eventTime` must be ISO 8601 UTC and `details` should include stage metadata (counts, artifact key, and diagnostic-safe failure code when relevant).

## Non-Functional Requirements

- Idempotent processing for duplicated queue deliveries.
- Deterministic handling of partial/failed Rekognition runs.
- Structured logs/metrics and error classification for DLQ triage.

## Mandatory Runtime Rule

- Initialize AWS SDK clients in module-global scope.
- Do not initialize AWS SDK clients inside Lambda handler code paths.

## Commands

- Install: `conda run -n conda_py_env_312 python -m pip install -r src/requirements.txt -r tests/requirements.txt`
- Test: `./scripts/run_tests.sh`
- Lint: `conda run -n conda_py_env_312 python -m ruff check src tests`
- Run: `sam build --template-file template.yaml`

## Open Decisions

- No-face policy final state before `MS3` rollout (`processing` hold vs terminal `failed` with specific code).
- Artifact retention lifecycle policy tuning.
