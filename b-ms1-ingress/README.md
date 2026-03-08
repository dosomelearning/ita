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
- Validate instructor-defined shared password (stored in DynamoDB).
- Reject invalid password requests before protected flow.
- Generate and return S3 presigned URL + upload metadata for accepted requests.
- Register initial upload state with state manager (or via agreed event/API contract).
- Emit structured logs and metrics for admission outcomes.

## Inbound / Outbound Contracts

- Inbound:
  - API Gateway request from frontend with shared password and upload context.
- Outbound:
  - Presigned URL response to frontend.
  - Optional registration event/state update to `b-ms4-statemgr`.
  - Upload target points to shared "uploaded photos" S3 bucket.

## Non-Functional Requirements

- API Gateway rate limiting is mandatory.
- Validation failure paths must be explicit and auditable.
- Keep credentials out of repo; use AWS profile-based auth for local tooling.

## Commands

- Install: `TBD (document once module tooling is scaffolded)`
- Test: `TBD`
- Lint: `TBD`
- Run: `TBD`

## Open Decisions

- Exact API request/response schema for upload-init.
- Password rotation/update workflow.
- Correlation ID format shared across downstream services.
- Final boundary for password table ownership (shared infra vs service-owned table).
