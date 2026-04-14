# T-021: Add Stack Status Helper Scripts

## Metadata

- Status: `in_progress`
- Created: `2026-04-14`
- Last Updated: `2026-04-14`
- Related Backlog Item: `T-021`
- Related Modules: `scripts/cfn_stack_report.sh`, `scripts/describe_ita_infra_stack.sh`, `scripts/describe_ita_ms1_ingress_stack.sh`, `scripts/describe_ita_ms2_detection_stack.sh`, `scripts/describe_ita_ms3_faces_stack.sh`, `scripts/describe_ita_ms4_statemgr_stack.sh`, `scripts/README.md`

## Context

The project needs repeatable and low-friction diagnostics for currently used CloudFormation stacks in the `dev` account. The goal is a script-per-stack entrypoint so stack checks are fast and consistent during development.

## Scope

In scope:

- Create root `scripts/` helper tooling for CloudFormation stack inspection.
- Provide one script per stack with clear names.
- Report stack summary, outputs, resources, and recent events using AWS CLI read-only calls.

Out of scope:

- Any AWS write operations (create/update/delete stacks).
- Deploy workflows or stack mutation scripts.

## AD Dependencies

- `AD-018` - IaC-only workflow still requires operational observability for stack state; helpers support that without console drift.
- `AD-021` - Shared platform resources in `b-infra` are part of the reported stack set.

## Acceptance Criteria

- [ ] Root `scripts/` includes one wrapper script per active stack.
- [ ] Wrapper scripts call shared logic with the correct default stack names.
- [ ] Shared script uses project AWS defaults (`dev`, `eu-central-1`, non-interactive flags).
- [ ] Output includes: stack summary, outputs, resources, and recent events.
- [ ] Documentation exists for helper usage syntax in `scripts/README.md`.

## Implementation Notes

Each wrapper sets a fixed default stack name and delegates to one shared reporter script to avoid duplication and keep output format aligned.

## Validation Evidence

- Command(s) run:
  - `cat b-ms1-ingress/samconfig.toml`
  - `cat b-ms2-detection/samconfig.toml`
  - `cat b-ms3-faces/samconfig.toml`
  - `cat b-ms4-statemgr/samconfig.toml`
  - `cat b-infra/scripts/deploy_infra.sh`
  - `cat docs/README.md`
- Manual checks:
  - Confirmed stack naming convention from module configs.
- Output summary:
  - Scripts created for `ita-infra`, `ita-ms1-ingress`, `ita-ms2-detection`, `ita-ms3-faces`, and `ita-ms4-statemgr`.
  - Usage syntax documented in `scripts/README.md`.

## Change Log

- `2026-04-14` - Initial draft.
