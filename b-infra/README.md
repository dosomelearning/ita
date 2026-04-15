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
`template-infra.yaml` is the deployment source of truth for these shared resources.
`b-infra` is the first stack in deployment order for this project.

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
- One shared processing S3 bucket used across services with prefixes:
  - `uploaded/`
  - `processed/`
    - `processed/faces/`
    - `processed/nofaces/`
  - `rekognition/`
  - `faces/`
- One dedicated access-logs S3 bucket for CloudFront logs (`cloudfront/` prefix).
- Shared event resources:
  - Uploaded photo notification queue + DLQ (boundary queue from S3 uploaded prefix).
  - Faces extraction queue + DLQ.
- System alarms SNS topic.
- Project-level logging/metrics/alarms baseline.

## Interfaces

- Inputs:
  - Environment/stage settings.
  - Service module wiring requirements.
- Outputs:
  - Resource names/ARNs/URLs consumed by `b-ms1-ingress`, `b-ms2-detection`, `b-ms3-faces`, `b-ms4-statemgr`, and `f-spa`.
  - Cross-stack outputs are exported with `Export` names using `${AWS::StackName}-<OutputKey>` pattern.

## Cross-Stack Output Strategy

- Export shared runtime wiring values from `b-infra` for service-stack consumption:
  - Shared processing bucket name.
  - Boundary queue ARNs/URLs and DLQ ARNs.
  - System alarms SNS topic ARN.
  - Frontend delivery outputs (CloudFront/DNS URL, distribution ID, hosting bucket).
- Keep environment/bootstrap identifiers as local deployment parameters (not imported from other stacks):
  - Hosted zone ID.
  - Domain name.
  - ACM certificate ARN.
- Rationale:
  - Runtime shared-resource identifiers should be centrally produced and consistently consumed.
  - Environment/account-specific bootstrap values remain deployment-context inputs and should stay outside cross-stack dependency contracts.
  - This avoids leaking environment bootstrap details into import contracts and keeps service templates focused on runtime dependencies.

## Current Template Decisions

- Template path: `b-infra/template-infra.yaml`.
- Domain/DNS defaults:
  - Hosted zone ID example: `ZXXXXXXXXXXXXXXX`
  - App hostname example: `ita.example.com`
  - ACM certificate ARN example (CloudFront/us-east-1): `arn:aws:acm:us-east-1:111122223333:certificate/00000000-0000-0000-0000-000000000000`
- Naming style:
  - Prefix `ita` + suffix parameter for globally unique resource names.
- CloudFront logging:
  - Logs are collected into a dedicated logs bucket under `cloudfront/`.
  - ACL-compatible bucket settings are applied only to the dedicated logs bucket to satisfy CloudFront log delivery requirements.
  - Shared processing bucket remains data-only and ACL-restricted with stricter defaults.
  - Glue/Athena log analytics are intentionally deferred for current phase.
  - In a more advanced/production-like setup, Glue/Athena would be added for access-pattern analysis.
- S3 prefix management:
  - CloudFormation does not create prefixes as first-class resources.
  - Prefixes are contract/keyspace conventions enforced by service object keys and policies.
- S3->SQS notification wiring:
  - Queue policy currently restricts by `aws:SourceAccount` to avoid CloudFormation circular dependency between bucket notifications and queue policy source-ARN references.
  - If stricter bucket-ARN binding is required later, implement notification setup via a two-step/custom-resource approach.

## Parameter File Workflow

- Keep real environment/account values outside git in local parameter JSON files.
- Example file (safe placeholders, committed): `b-infra/params/dev.parameters.example.json`.
- Local private file (ignored): `b-infra/params/dev.parameters.json`.

Example local parameter file format (`create-stack`/`update-stack`):

```json
[
  {"ParameterKey":"HostedZoneId","ParameterValue":"ZXXXXXXXXXXXXXXX"},
  {"ParameterKey":"DomainName","ParameterValue":"ita.example.com"},
  {"ParameterKey":"ProjectPrefix","ParameterValue":"ita"},
  {"ParameterKey":"RandomSuffix","ParameterValue":"dev001"},
  {"ParameterKey":"AcmCertificateArn","ParameterValue":"arn:aws:acm:us-east-1:111122223333:certificate/00000000-0000-0000-0000-000000000000"},
  {"ParameterKey":"CostAllocationTagValue","ParameterValue":"ita"}
]
```

Example command pattern:

```bash
AWS_CLI_AUTO_PROMPT=off AWS_PAGER="" AWS_EC2_METADATA_DISABLED=true \
aws cloudformation update-stack \
  --profile dev \
  --region eu-central-1 \
  --stack-name ita-infra \
  --template-body file://b-infra/template-infra.yaml \
  --parameters file://b-infra/params/dev.parameters.json \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --no-cli-pager
```

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
- Run:
  - `./b-infra/scripts/deploy_infra.sh`
  - Optional custom params file:
    - `./b-infra/scripts/deploy_infra.sh ./b-infra/params/dev.parameters.json`
  - Optional env overrides:
    - `STACK_NAME=ita-infra AWS_PROFILE=dev AWS_REGION=eu-central-1 ./b-infra/scripts/deploy_infra.sh`
  - Deploy a generated test `index.html` and fetch it with curl:
    - `./b-infra/scripts/deploy_test_index.sh`
  - Initialize shared data-bucket prefix markers (idempotent):
    - `./b-infra/scripts/init_data_prefixes.sh`

## Open Decisions

- Alarm threshold tuning and SNS subscription targets.
- Optional future observability analytics expansion (Glue/Athena).
