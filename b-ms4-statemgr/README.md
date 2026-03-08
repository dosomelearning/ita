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

- Install: `TBD (document once module tooling is scaffolded)`
- Test: `TBD`
- Lint: `TBD`
- Run: `TBD`

## Open Decisions

- Canonical state machine and transition rules.
- Read API shape for polling vs batched status retrieval.
- Leaderboard aggregation model and refresh strategy.
- State table ownership split (service-owned by MS4 vs explicitly shared table in `b-infra`).
