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
  - SPA upload CORS origin.
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

## Environment Config Workflow

- Keep real environment/account values outside git in local environment JSON files.
- Example files (safe placeholders, committed):
  - `b-infra/params/dev.parameters.example.json`
  - `b-infra/params/sandbox2.parameters.example.json`
- Local private files (ignored):
  - `b-infra/params/dev.parameters.json`
  - `b-infra/params/sandbox2.parameters.json`

Example local environment config format:

```json
{
  "stackName": "ita-infra",
  "awsProfile": "dev",
  "awsRegion": "eu-central-1",
  "parameters": [
    {"ParameterKey":"HostedZoneId","ParameterValue":"ZXXXXXXXXXXXXXXX"},
    {"ParameterKey":"DomainName","ParameterValue":"ita.example.com"},
    {"ParameterKey":"ProjectPrefix","ParameterValue":"ita"},
    {"ParameterKey":"RandomSuffix","ParameterValue":"dev001"},
    {"ParameterKey":"AcmCertificateArn","ParameterValue":"arn:aws:acm:us-east-1:111122223333:certificate/00000000-0000-0000-0000-000000000000"},
    {"ParameterKey":"SpaAllowedOrigin","ParameterValue":"https://ita.example.com"},
    {"ParameterKey":"CostAllocationTagValue","ParameterValue":"ita"}
  ]
}
```

Example command pattern:

```bash
./b-infra/scripts/deploy_infra.sh ./b-infra/params/dev.parameters.json
```

Required top-level config fields:

- `stackName` - CloudFormation stack name for this environment.
- `awsProfile` - AWS CLI profile to use for all commands in this environment.
- `awsRegion` - Deployment region for the shared stack. Current baseline: `eu-central-1`.
- `parameters` - CloudFormation parameter array passed to `template-infra.yaml`.

Required CloudFormation parameters:

- `HostedZoneId` - Hosted zone where the app alias record will be created.
- `DomainName` - Public app hostname served by CloudFront.
- `ProjectPrefix` - Prefix used in globally unique resource names.
- `RandomSuffix` - Environment-specific uniqueness suffix for bucket/queue/topic names.
- `AcmCertificateArn` - ACM certificate ARN in `us-east-1` for the app hostname.
- `SpaAllowedOrigin` - HTTPS origin allowed by shared processing bucket CORS.
- `CostAllocationTagValue` - Value used for cost-allocation tagging.

## Deployment Model

`b-infra` now assumes one mandatory environment config file per deployment target.
That file is the only supported input to the operational scripts in this module.

This avoids splitting deployment context across:

- raw CloudFormation parameter arrays
- shell environment overrides
- script defaults

The intended model is:

- one stack per environment
- one AWS CLI profile per environment
- one environment config JSON file per environment
- one app hostname per environment

Current examples in this repository:

- `dev` environment:
  - config file: `b-infra/params/dev.parameters.json`
  - stack name: `ita-infra`
  - hostname: `ita.dosomelearning.com`
- `sandbox2` environment:
  - config file: `b-infra/params/sandbox2.parameters.json`
  - stack name: `ita-infra-sandbox2`
  - hostname: `ita.sandbox2.dosomelearning.com`

## New Account Deployment Flow

For a completely separate AWS account, the recommended path is:

1. Create a public Route53 hosted zone in the new account for a delegated subdomain.
2. Add parent-zone NS delegation from the original domain owner.
3. Request an ACM certificate in `us-east-1` for the target hostname or wildcard.
4. Complete ACM DNS validation in the delegated hosted zone.
5. Fill the environment config JSON with:
   - target stack name
   - target AWS CLI profile
   - hosted zone ID
   - app hostname
   - issued ACM ARN
   - CORS origin matching the app hostname
6. Deploy `b-infra`.
7. After stack completion, run the helper scripts against the same environment config.

For the currently documented second-account environment, that means:

- delegated zone: `sandbox2.dosomelearning.com`
- app hostname: `ita.sandbox2.dosomelearning.com`
- certificate scope: wildcard `*.sandbox2.dosomelearning.com` or exact app hostname
- certificate region: `us-east-1`

This preserves the original environment because the second account uses:

- a different AWS profile
- a different stack name
- a different hosted zone
- a different app hostname
- separate globally named resources through its own `RandomSuffix`

## Operational Script Behavior

All operational scripts in `b-infra/scripts/` now require the same mandatory environment config JSON file:

- `deploy_infra.sh`
- `init_data_prefixes.sh`
- `deploy_test_index.sh`

They all read:

- `stackName`
- `awsProfile`
- `awsRegion`

from the config file and do not rely on `dev` shell defaults anymore.

`deploy_test_index.sh` and `init_data_prefixes.sh` are output-dependent helper scripts.
They expect the target stack to be complete before use.
If the stack is still in `CREATE_IN_PROGRESS` or similar transitional states, they fail intentionally rather than guessing at incomplete outputs.

## Script Invocation Examples

Deploy the shared stack for `dev`:

```bash
./b-infra/scripts/deploy_infra.sh ./b-infra/params/dev.parameters.json
```

Deploy the shared stack for `sandbox2`:

```bash
./b-infra/scripts/deploy_infra.sh ./b-infra/params/sandbox2.parameters.json
```

Initialize shared data-bucket prefixes for `dev` after stack completion:

```bash
./b-infra/scripts/init_data_prefixes.sh ./b-infra/params/dev.parameters.json
```

Initialize shared data-bucket prefixes for `sandbox2` after stack completion:

```bash
./b-infra/scripts/init_data_prefixes.sh ./b-infra/params/sandbox2.parameters.json
```

Deploy a generated `index.html` test page to the `dev` hosting bucket after stack completion:

```bash
./b-infra/scripts/deploy_test_index.sh ./b-infra/params/dev.parameters.json
```

Deploy a generated `index.html` test page to the `sandbox2` hosting bucket after stack completion:

```bash
./b-infra/scripts/deploy_test_index.sh ./b-infra/params/sandbox2.parameters.json
```

The normal operational order for a new environment is:

1. `deploy_infra.sh`
2. `init_data_prefixes.sh`
3. `deploy_test_index.sh`

## Outputs and Verification

On successful stack completion, the most important outputs are:

- `AppUrlCloudFront`
- `AppUrlDns`
- `CloudFrontDistributionId`
- `WebHostingBucketName`
- `SharedProcessingBucketName`

Practical verification after deployment:

- CloudFormation stack reaches `CREATE_COMPLETE` or `UPDATE_COMPLETE`.
- The delegated app hostname resolves publicly.
- The hostname serves through CloudFront using the configured ACM certificate.
- The hosting bucket accepts the test `index.html` upload.
- The shared processing bucket prefix markers can be initialized successfully.

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
  - `./b-infra/scripts/deploy_infra.sh ./b-infra/params/dev.parameters.json`
  - `./b-infra/scripts/deploy_infra.sh ./b-infra/params/sandbox2.parameters.json`
  - `./b-infra/scripts/init_data_prefixes.sh ./b-infra/params/dev.parameters.json`
  - `./b-infra/scripts/init_data_prefixes.sh ./b-infra/params/sandbox2.parameters.json`
  - `./b-infra/scripts/deploy_test_index.sh ./b-infra/params/dev.parameters.json`
  - `./b-infra/scripts/deploy_test_index.sh ./b-infra/params/sandbox2.parameters.json`

## Open Decisions

- Alarm threshold tuning and SNS subscription targets.
- Optional future observability analytics expansion (Glue/Athena).
