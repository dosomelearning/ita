# T-036: Plan Second-Account Infra Deployment

## Metadata

- Status: `in_progress`
- Created: `2026-05-07`
- Last Updated: `2026-05-07`
- Related Backlog Item: `T-036`
- Related Modules: `b-infra/README.md`, `b-infra/template-infra.yaml`, `b-infra/scripts/deploy_infra.sh`

## Context

The project needs a second deployment in a completely separate AWS account without modifying or removing the existing environment. The current `b-infra` stack assumes a Route53 hosted zone already exists in the target account, which becomes a deployment concern when moving to a new account and introducing a new URL under `sandbox2.dosomelearning.com`.

## Scope

In scope:

- Review current `b-infra` same-account DNS/TLS assumptions.
- Define a safe approach for deploying shared infra into a second AWS account while keeping the current environment intact.
- Decide what must remain deployment-time input versus what should become template-controlled for DNS/TLS bootstrap.

Out of scope:

- Deploying microservice stacks or frontend assets to the new account.
- Removing, renaming, or replacing the current deployment.

## AD Dependencies

- `AD-014` - The frontend must remain hosted from S3 behind CloudFront, so the second environment still needs equivalent edge delivery.
- `AD-018` - Any environment change must stay in the IaC workflow rather than relying on console-only setup.
- `AD-021` - Domain, DNS, and TLS remain shared platform concerns owned by `b-infra`, which is the core decision under review here.

## Acceptance Criteria

- [ ] Current `b-infra` deployment assumptions for hosted zone and certificate ownership are documented.
- [ ] A recommended second-account deployment approach is defined that preserves the existing environment.
- [ ] Required template/script adaptations are identified and separated from one-time account bootstrap steps.
- [ ] DNS ownership implications for `sandbox2.dosomelearning.com` and `ita.sandbox2.dosomelearning.com` are made explicit.

## Implementation Notes

The main design question is whether `b-infra` should continue requiring a pre-existing hosted zone and certificate as inputs, or whether it should optionally own some bootstrap resources for a new account. Any change must preserve the current environment contract and avoid forcing a migration on the existing deployment.

Current implemented direction:

- Keep hosted zone and ACM certificate as deployment-time inputs.
- Use one mandatory environment config JSON file per target environment.
- Read stack name, AWS profile, and region from that file in all `b-infra` operational scripts.
- Keep Route53 alias record creation in `b-infra` so the app hostname is created automatically after successful stack deployment.
- Parameterize SPA upload CORS origin so the original deployment and second-account deployment can coexist safely with different hostnames.

## Validation Evidence

- Command(s) run:
  - `cat README.md`
  - `cat b-infra/README.md`
  - `cat b-infra/template-infra.yaml`
  - `cat b-infra/scripts/deploy_infra.sh`
  - `cat b-infra/scripts/init_data_prefixes.sh`
  - `cat b-infra/scripts/deploy_test_index.sh`
  - `cat b-infra/params/dev.parameters.example.json`
  - `cat docs/tasks/README.md`
  - `cat docs/system-checklist.md`
  - `cat ARCHITECTURE.md`
  - `dig NS sandbox2.dosomelearning.com +short`
  - `dig +trace NS sandbox2.dosomelearning.com`
  - `dig ita.sandbox2.dosomelearning.com A`
  - `dig _c799383298a6e8964dbb5ced820ceb56.sandbox2.dosomelearning.com CNAME`
  - `AWS_CLI_AUTO_PROMPT=off AWS_PAGER="" AWS_EC2_METADATA_DISABLED=true aws acm describe-certificate --profile sandbox2 --region us-east-1 --certificate-arn arn:aws:acm:us-east-1:508537814566:certificate/2f2906ed-d27d-4919-8a11-80a02ebeace3 --no-cli-pager`
- Manual checks:
  - Confirmed the current template expects `HostedZoneId`, `DomainName`, and `AcmCertificateArn` as existing deployment inputs.
  - Confirmed public NS delegation for `sandbox2.dosomelearning.com`.
  - Confirmed ACM DNS validation record was publicly resolvable.
  - Confirmed the wildcard ACM certificate in the new account was `ISSUED`.
  - Confirmed the new `b-infra` stack deployment completed successfully in the second account.
- Output summary:
  - `b-infra` now supports per-environment deployment through one mandatory environment config JSON file.
  - Helper scripts were aligned with the same config contract as `deploy_infra.sh`.
  - CORS origin is parameterized, allowing `dev` and `sandbox2` hostnames to coexist safely.
  - Second-account deployment model was validated with delegated DNS, issued ACM certificate, and successful `b-infra` stack deployment.

## Change Log

- `2026-05-07` - Initial draft.
- `2026-05-07` - Documented implemented second-account deployment model, DNS/TLS validation, and script contract changes.
