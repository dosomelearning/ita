# Scripts Usage

This document describes usage syntax for root-level helper scripts under `scripts/`.

## Testing and Smoke Checks

Centralized testing and diagnostics strategy is documented in:

- [`../docs/testing/README.md`](../docs/testing/README.md)

Primary test runner entrypoints:

- `./scripts/test_local.sh` - local deterministic baseline
- `./scripts/test_live_basic.sh` - live contract/envelope checks
- `./scripts/test_live_e2e.sh` - optional live e2e smoke (`MS1` init + upload + `MS4` poll)
- `./scripts/smoke_check.sh` - tier orchestrator (`local`, `live-basic`, `live-e2e`, `all`)
- `./scripts/test_all.sh` - alias for `smoke_check --tier all`
- `./scripts/render_test_snapshot.sh` - render markdown snapshot from latest JSON test reports

Central test config files:

- `./scripts/testing.env` - local source of truth for endpoints (not tracked)
- `./scripts/testing.env.local` - optional local overrides
- `./scripts/testing.env.example` - tracked template with empty values

All testing scripts write JSON summaries under:

- `tmp/test-reports/`

Default snapshot output:

- `docs/testing/latest-manual-run.md`

## CloudFormation Stack Inspection

The stack inspection helpers are read-only wrappers around AWS CloudFormation `describe-*` APIs.

Default environment assumptions:

- AWS profile: `dev`
- AWS region: `eu-central-1`
- Non-interactive AWS CLI flags enabled by script

### Available Wrapper Scripts

- `./scripts/describe_ita_infra_stack.sh`
- `./scripts/describe_ita_ms1_ingress_stack.sh`
- `./scripts/describe_ita_ms2_detection_stack.sh`
- `./scripts/describe_ita_ms3_faces_stack.sh`
- `./scripts/describe_ita_ms4_statemgr_stack.sh`

### Basic Usage

Run a stack report with defaults:

```bash
./scripts/describe_ita_ms4_statemgr_stack.sh
```

Run with explicit AWS profile and region overrides:

```bash
AWS_PROFILE=dev AWS_REGION=eu-central-1 ./scripts/describe_ita_infra_stack.sh
```

Limit number of printed recent events:

```bash
EVENT_LIMIT=40 ./scripts/describe_ita_ms1_ingress_stack.sh
```

Override wrapper default stack name (advanced):

```bash
STACK_NAME=ita-ms4-statemgr ./scripts/describe_ita_ms4_statemgr_stack.sh
```

### Shared Reporter Script

The wrapper scripts delegate to:

- `./scripts/cfn_stack_report.sh <stack-name>`

Direct invocation syntax:

```bash
./scripts/cfn_stack_report.sh ita-ms2-detection
```

### Report Sections

Each run prints:

1. Stack summary (`StackStatus`, IDs, timestamps, description)
2. Stack outputs
3. Stack resources
4. Recent stack events (latest first)
