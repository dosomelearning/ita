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

## Non-Functional Requirements

- Idempotent processing for duplicated queue deliveries.
- Deterministic handling of partial/failed Rekognition runs.
- Structured logs/metrics and error classification for DLQ triage.

## Commands

- Install: `TBD (document once module tooling is scaffolded)`
- Test: `TBD`
- Lint: `TBD`
- Run: `TBD`

## Open Decisions

- Canonical manifest schema between MS2 and MS3.
- Error taxonomy and retry policy boundaries.
- Artifact retention strategy.
- Queue ownership split if some event resources remain shared in `b-infra`.
