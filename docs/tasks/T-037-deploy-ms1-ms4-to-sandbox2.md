# T-037 Deploy MS1-MS4 to sandbox2

- Related Backlog Item: `T-037`
- Status: `done`
- Area: `Deployment`

## Summary

Deployed `b-ms1-ingress`, `b-ms2-detection`, `b-ms3-faces`, and `b-ms4-statemgr` into the additional `sandbox2` environment, reusing the documented separate-environment model already established for `b-infra`.

## Scope

- Refactor all backend SAM templates to import shared values from `b-infra` and service-owned values from `MS4` instead of duplicating environment-specific identifiers in `samconfig.toml`.
- Add `sandbox2` SAM config sections for `MS1`, `MS2`, `MS3`, and `MS4`, then validate deployment in both `default` and `sandbox2`.
- Add frontend deployment target configs under `f-spa/config/` plus scripts to populate resolved values from CloudFormation and deploy the SPA per environment.
- Validate end-to-end deployment readiness in `sandbox2`, including the shared password SSM parameter path `/ita/class/shared-password`.

## Outcome

- `b-infra` exports now include `AppDomainName` and `SpaAllowedOrigin` for downstream imports.
- `MS4` imports shared frontend values from `b-infra`, exports `ApiEndpoint`, and deploys via `sam deploy --config-env default|sandbox2`.
- `MS1`, `MS2`, and `MS3` import shared bucket/queue values from `b-infra` and `MS4` `ApiEndpoint` from the owning service stack.
- Legacy manual `parameter_overrides` lines were retained as comments in backend SAM configs/templates for rollout traceability.
- `f-spa` now uses per-environment JSON config files with separate `inputs` and `resolved` sections, a populate script, and a mandatory-config deploy script.

## AD Dependencies

- None identified yet; deployment should follow the existing documented ownership and cross-stack-output model unless service-specific constraints require an architecture decision.
