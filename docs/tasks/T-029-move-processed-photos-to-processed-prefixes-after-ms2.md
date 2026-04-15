# T-029: Move Processed Photos to `processed/` Prefixes After MS2

## Metadata

- Status: `done`
- Created: `2026-04-15`
- Last Updated: `2026-04-15`
- Related Backlog Item: `T-029`
- Related Modules: `b-ms2-detection/src/service.py`, `b-ms2-detection/template.yaml`, `b-ms2-detection/tests/unit/test_service.py`, `b-ms2-detection/README.md`, `b-ms3-faces/README.md`, `b-infra/README.md`, `README.md`, `docs/process/photo-upload-processing-sequence.md`, `img/ita-photo-flow-sequence.mmd`

## Context

Current `MS2` processing reads from `uploaded/` and leaves source photos there. Project lifecycle intent requires clearer separation after detection processing. The source object should be moved out of ingress prefix once `MS2` is done, and downstream contracts must use the moved object key.

## Scope

In scope:

- After `MS2` detection, move source image from `uploaded/` to:
  - `processed/faces/{sessionId}/{uploadId}.<ext>` when detected faces > 0
  - `processed/nofaces/{sessionId}/{uploadId}.<ext>` when detected faces = 0
- Update `MS2` event details/artifact/queue message references to the moved key.
- Update `MS2` IAM policy to allow required S3 copy/delete operations.
- Add/update unit tests for move behavior and downstream key references.
- Update module docs to describe the new prefix transition behavior.

Out of scope:

- `MS3` extraction implementation itself.
- End-of-class bulk cleanup automation.

## AD Dependencies

- `AD-003` - Queue-driven async stage boundaries remain unchanged.
- `AD-006` - Data lifecycle constraints drive stricter object-state movement discipline.
- `AD-009` - Single processing bucket with prefix isolation; this task formalizes additional prefix lifecycle semantics.
- `AD-012` - Detection remains in `MS2`, now with explicit post-detection object relocation.

## Acceptance Criteria

- [x] `MS2` moves processed source object out of `uploaded/` into `processed/faces` or `processed/nofaces`.
- [x] `MS2` extraction queue payload references moved source key.
- [x] `MS2` detection artifact references moved source key.
- [x] `MS2` template policies include necessary S3 permissions for move semantics.
- [x] Unit tests verify move destination selection and downstream reference correctness.
- [x] `MS2` and `MS3` README contracts reflect new source-key expectations.

## Implementation Notes

- S3 move semantics are implemented as `CopyObject` + `DeleteObject`.
- Move should occur only after detection result is known so destination branch can be selected.
- Failure in move is treated as retriable dependency failure.

## Validation Evidence

- Command(s) run:
  - `cd b-ms2-detection && ./scripts/run_tests.sh`
  - `./scripts/test_local.sh`
- Manual checks:
  - Confirmed both outcome branches map to distinct target prefixes (`processed/faces`, `processed/nofaces`).
  - Confirmed process documentation and Mermaid sequence source include post-detection move semantics and updated downstream source-key references.
- Output summary:
  - `MS2` now relocates source objects after detection and emits downstream references against moved keys.
  - Local centralized test suite passed (`ms1`, `ms2`, `ms4`, `spa unit`, `spa build`).

## Change Log

- `2026-04-15` - Initial task file created.
- `2026-04-15` - Implemented post-detection relocation (`uploaded -> processed/faces|nofaces`) and updated downstream key references/tests/docs.
