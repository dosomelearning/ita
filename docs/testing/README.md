# Testing and Diagnostics Strategy

This document is the central source of truth for project verification and operational diagnostics.

## Goals

- Make test coverage and runnable checks visible from one place.
- Provide centralized root-level commands for repeatable runs.
- Distinguish local deterministic checks from network/live checks.
- Track diagnostics commands used to inspect deployed stack/runtime state.

## Test Tiers

- `local`:
  - Deterministic and no network dependency.
  - Safe baseline before implementation checkpoints.
- `live-basic`:
  - Calls deployed APIs for contract/error-envelope validation.
  - Does not require valid class password.
- `live-e2e`:
  - Requires valid class password.
  - Runs `MS1` init + presigned upload + `MS4` polling smoke flow.
  - Current expected terminal status is `queued` until `MS2`/`MS3` are implemented.

## Centralized Runner Scripts

- `./scripts/test_local.sh`
- `./scripts/test_live_basic.sh`
- `./scripts/test_live_e2e.sh`
- `./scripts/smoke_check.sh`
- `./scripts/test_all.sh`
- `./scripts/render_test_snapshot.sh`

## Central Test Configuration

Testing scripts load configuration from:

1. `scripts/testing.env` (local source of truth, not tracked)
2. `scripts/testing.env.local` (optional local override, not tracked)
3. Environment variables passed at command invocation (highest precedence)

Tracked template:

- `scripts/testing.env.example` (empty values)

Main variables:

- `MS1_API_BASE_URL`
- `MS4_API_BASE_URL`
- `SMOKE_CLASS_PASSWORD` (optional; required for `live-e2e`)
- `SMOKE_NICKNAME` (default `smokeuser`; must satisfy backend nickname validation)
- `SMOKE_EXPECTED_FINAL_STATUS` (currently `queued`)

All scripts write JSON run reports to:

- `tmp/test-reports/`

Latest alias:

- `tmp/test-reports/latest-<script>.json`

Markdown snapshot generator:

- `./scripts/render_test_snapshot.sh`
- Default output: `docs/testing/latest-manual-run.md`

## Module Test Inventory

| Module | Type | Command | Prereqs | Duration | Notes |
|---|---|---|---|---|---|
| `b-ms1-ingress` | Unit | `./b-ms1-ingress/scripts/run_tests.sh` | Conda env `conda_py_env_312` | Short | API/domain/service/handler tests |
| `b-ms2-detection` | Unit | `./b-ms2-detection/scripts/run_tests.sh` | Conda env `conda_py_env_312` | Short | Queue parser/service flow/API/handler tests |
| `b-ms4-statemgr` | Unit | `./b-ms4-statemgr/scripts/run_tests.sh` | Conda env `conda_py_env_312` | Short | API/domain/repository/service tests |
| `b-ms4-statemgr` | Live integration | `MS4_API_BASE_URL=<url> ./b-ms4-statemgr/scripts/run_integration_tests.sh` | Deployed API URL; network | Short | Missing-upload envelope behavior |
| `f-spa` | Unit | `cd f-spa && npm test` | Node deps installed | Short | Gateway/mode behavior tests |
| `f-spa` | Build | `cd f-spa && npm run build` | Node deps installed | Short | Production build sanity |

## Centralized Command Usage

### Local baseline

```bash
./scripts/test_local.sh
```

### Live contract baseline

```bash
./scripts/test_live_basic.sh
```

### Optional live e2e smoke

```bash
SMOKE_CLASS_PASSWORD='<class-password>' \
./scripts/test_live_e2e.sh
```

### Tiered smoke orchestrator

```bash
./scripts/smoke_check.sh --tier local
./scripts/smoke_check.sh --tier live-basic
./scripts/smoke_check.sh --tier live-e2e
./scripts/smoke_check.sh --tier all
```

Behavior note:

- `--tier all` runs `local` and `live-basic` always.
- `live-e2e` is executed only when `SMOKE_CLASS_PASSWORD` is set; otherwise it is explicitly skipped.

`./scripts/test_all.sh` is a convenience alias for:

```bash
./scripts/smoke_check.sh --tier all
```

Generate a readable markdown snapshot from latest JSON reports:

```bash
./scripts/render_test_snapshot.sh
# or custom output path:
./scripts/render_test_snapshot.sh docs/testing/my-run-2026-04-15.md
```

## Diagnostics

These are read-only stack diagnostics helpers used during implementation and deployment reflection:

- `./scripts/describe_ita_infra_stack.sh`
- `./scripts/describe_ita_ms1_ingress_stack.sh`
- `./scripts/describe_ita_ms2_detection_stack.sh`
- `./scripts/describe_ita_ms3_faces_stack.sh`
- `./scripts/describe_ita_ms4_statemgr_stack.sh`
- `./scripts/cfn_stack_report.sh <stack-name>`

Diagnostics are complementary to tests:

- tests validate expected behavior/contract;
- diagnostics inspect deployed stack composition/status/events.

## Status Interpretation (Current Phase)

- Green baseline:
  - `test_local.sh` pass
  - `test_live_basic.sh` pass
- Live e2e (`test_live_e2e.sh`):
  - `queued` is currently expected and treated as pass while `MS2`/`MS3` runtime deployment is pending.
  - expected behavior will be updated once processing services are deployed and active.
