# b-ms3-faces

Face extraction microservice.

## Related Docs

- [`../README.md`](../README.md) (project overview and boundaries)
- [`../AGENTS.md`](../AGENTS.md) (project workflow and guardrails)
- [`../b-infra/README.md`](../b-infra/README.md)
- [`../b-ms1-ingress/README.md`](../b-ms1-ingress/README.md)
- [`../b-ms2-detection/README.md`](../b-ms2-detection/README.md)
- [`../b-ms4-statemgr/README.md`](../b-ms4-statemgr/README.md)
- [`../f-spa/README.md`](../f-spa/README.md)

## Purpose

`b-ms3-faces` consumes detection output, extracts face crops, stores resulting images, and reports extraction progress/results.

## Ownership Model

- This microservice owns its own SAM template and service resources.
- Shared foundational resources are consumed from `b-infra` outputs.

## Responsibilities

- Consume face-extraction jobs from SQS queue (with DLQ fallback).
- Read detection manifest/artifacts produced by `b-ms2-detection`.
- Extract per-face images from source photo(s).
- Store extracted face images in shared "extracted faces" storage.
- Report extraction lifecycle status (`started`, `completed`, `failed`) to state manager.

## Inbound / Outbound Contracts

- Inbound:
  - SQS message from faces-extraction queue.
  - Detection manifest/artifacts from shared storage.
- Outbound:
  - Extracted face image artifacts.
  - Status updates and output references to `b-ms4-statemgr`.

## Non-Functional Requirements

- Idempotent extraction for duplicate queue messages.
- Stable output naming to avoid artifact collisions.
- Clear recoverability path for failed jobs via DLQ replay.

## Commands

- Install: `conda run -n conda_py_env_312 python -m pip install -r src/requirements.txt -r tests/requirements.txt`
- Test: `./scripts/run_tests.sh`
- Lint: `conda run -n conda_py_env_312 python -m ruff check src tests`
- Run: `sam build --template-file template.yaml`

## Open Decisions

- Exact face crop quality/resolution policy.
- Output object key scheme and metadata model.
- Maximum per-image face count handling.
- Queue ownership split if some event resources remain shared in `b-infra`.
