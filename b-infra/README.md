# b-infra

Shared infrastructure module for the `4-ita` system.

## Related Docs

- [`../README.md`](../README.md) (project overview and boundaries)
- [`../AGENTS.md`](../AGENTS.md) (project workflow and guardrails)
- [`../b-ms1-ingress/README.md`](../b-ms1-ingress/README.md)
- [`../b-ms2-detection/README.md`](../b-ms2-detection/README.md)
- [`../b-ms3-faces/README.md`](../b-ms3-faces/README.md)
- [`../b-ms4-statemgr/README.md`](../b-ms4-statemgr/README.md)
- [`../f-spa/README.md`](../f-spa/README.md)

## Purpose

This module owns only project-foundational AWS infrastructure shared across services and frontend delivery.
Service-owned compute and API resources are not defined here.

## Responsibilities

- Define foundational resources used across modules.
- Own frontend edge and hosting base resources (CloudFront, hosting S3, Route53, ACM).
- Own shared data/event resources used by multiple services (for example shared S3 buckets and shared queue infrastructure when intentionally shared).
- Provide baseline observability/logging foundations used project-wide.
- Expose outputs needed by service modules and deployment scripts.

## Architecture Scope (from current diagram + root README)

- CloudFront distribution for frontend delivery.
- Frontend hosting S3 bucket.
- Route53 DNS entries and ACM certificates.
- Shared S3 buckets used across services:
  - Uploaded photos.
  - Rekognition artifacts.
  - Extracted faces.
- Shared event resources when cross-service ownership is required:
  - Uploaded photo notification queue + DLQ.
  - Faces extraction queue + DLQ.
- Project-level logging/metrics/alarms baseline.

## Interfaces

- Inputs:
  - Environment/stage settings.
  - Service module wiring requirements.
- Outputs:
  - Resource names/ARNs/URLs consumed by `b-ms1-ingress`, `b-ms2-detection`, `b-ms3-faces`, `b-ms4-statemgr`, and `f-spa`.

## Explicit Non-Ownership

- No service Lambda function resources.
- No microservice-specific API Gateway definitions.
- No service-owned DynamoDB tables unless a table is explicitly designated as shared foundational infrastructure.

## Constraints

- Region baseline: `eu-central-1`.
- API Gateway endpoints must enforce throttling/rate limits.
- No Cognito in this project.
- Do not run AWS write operations without explicit approval.

## Commands

- Install: `TBD (document once module tooling is scaffolded)`
- Test: `TBD`
- Lint: `TBD`
- Run: `TBD`

## Open Decisions

- Final list of resources classified as shared vs service-owned.
- Naming/tagging convention for all resources.
- Alarm set and SLO/SLA thresholds.
