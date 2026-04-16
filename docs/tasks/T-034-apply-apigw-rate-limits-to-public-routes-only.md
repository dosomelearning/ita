# T-034: Apply APIGW Rate Limits to Public Routes Only

## Metadata

- Status: `in_progress`
- Created: `2026-04-16`
- Last Updated: `2026-04-16`
- Related Backlog Item: `T-034`
- Related Modules: `b-ms1-ingress/template.yaml`, `b-ms4-statemgr/template.yaml`

## Context

The project requires rate limiting on user-exposed API paths while internal service-to-service endpoints remain unrestricted by API Gateway throttling.
WAF is intentionally out of scope for this project.

## Scope

In scope:

- Configure API Gateway throttling only for public `/v1/*` routes in `MS1` and `MS4`.
- Keep internal `/internal/*` routes without API Gateway throttling configuration.
- Parameterize limits in SAM templates for simple tuning.

Out of scope:

- WAF rate-based rules.
- Changes to IAM auth model on internal routes.

## Acceptance Criteria

- [x] `MS1` public init route has explicit throttling limits.
- [x] `MS4` public read routes have explicit throttling limits.
- [x] `MS4` internal routes remain IAM-authenticated and non-throttled at APIGW layer.
- [x] Limits reflect the agreed "double rates" profile.

## Validation Evidence

- Executed template validation:
  - `sam validate --template-file b-ms1-ingress/template.yaml` -> pass
  - `sam validate --template-file b-ms4-statemgr/template.yaml` -> pass
- Executed post-deploy live checks:
  - `./scripts/test_live_basic.sh` -> pass (`5/5`)
  - `./scripts/test_live_e2e.sh` -> pass (`4/4`)

## Change Log

- `2026-04-16` - Created task and applied route-level APIGW throttling to public endpoints with doubled limits.
