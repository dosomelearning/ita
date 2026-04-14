# Scripts Usage

This document describes usage syntax for root-level helper scripts under `scripts/`.

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
