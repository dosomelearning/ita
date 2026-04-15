# T-031: Implement MS3 Extraction Phase 1 and SPA Face-Count Summary

## Metadata

- Status: `in_progress`
- Created: `2026-04-16`
- Last Updated: `2026-04-16`
- Related Backlog Item: `T-031`
- Related Modules: `b-ms3-faces/src/main.py`, `b-ms3-faces/src/api.py`, `b-ms3-faces/src/domain.py`, `b-ms3-faces/src/service.py`, `b-ms3-faces/src/ms4_client.py`, `b-ms3-faces/template.yaml`, `b-ms3-faces/tests/unit/*.py`, `f-spa/src/stateGateway.ts`, `f-spa/src/App.tsx`, `f-spa/src/index.css`, `docs/process/photo-upload-processing-sequence.md`, `b-ms3-faces/README.md`

## Context

`MS2` already detects faces and emits `faces-extraction.v1` jobs, but `MS3` is still scaffold-only.  
This phase implements real extraction and a lightweight SPA outcome visualization: show the total detected/extracted face count after successful processing, without rendering face thumbnails yet.

## Scope

In scope:

- Implement `MS3` SQS consumer for `faces-extraction.v1`.
- Load canonical detection artifact and crop faces from moved `processed/faces/*` source image.
- Store deterministic extracted objects under `faces/{sessionId}/{uploadId}/...`.
- Post `MS4` extraction completion/failure events with `producer=ms3`.
- Include `results.faceCount` in completed event payload.
- Update SPA submit status panel to show large face-count summary on successful completion.
- Expose completed face-count in Home/Activity feed rows with success-highlight styling.
- Add/extend unit tests for `MS3` + SPA status gateway parsing.

Out of scope:

- Rendering extracted face images in SPA.
- Pagination/filtering changes in activity feed.
- Any architecture changes to queue topology.

## AD Dependencies

- `AD-010` - Pipeline stages are asynchronous and event-driven; `MS3` must consume queue jobs and emit stage outcomes.
- `AD-016` - `MS4` remains canonical read model/state projection for SPA.
- `AD-017` - Queue contract/version behavior and retry/DLQ semantics remain contract-driven.

## Acceptance Criteria

- [x] `MS3` consumes `faces-extraction.v1` queue records and validates required fields.
- [x] `MS3` writes extracted face crops to deterministic `faces/` keys.
- [x] `MS3` emits `extraction_completed` (`statusAfter=completed`) with `results.faceCount`.
- [x] `MS3` emits `extraction_failed` (`statusAfter=failed`) for non-success path.
- [x] SPA displays a green face-count summary block in submit status view when completion returns face count.
- [x] Unit tests pass for updated `MS3` and SPA modules.

## Implementation Notes

- Keep AWS SDK client initialization in module-global scope for Lambda cold-start efficiency.
- Use deterministic event time/value for completion/failure events to improve duplicate-delivery idempotency.
- Keep extraction outputs deterministic by stable naming (`face-001.jpg`, ...).
- Preserve existing no-face behavior: no `MS3` invocation for `detectedFaces=0` path.

## Validation Evidence

- Command(s) run:
  - `cd b-ms3-faces && ./scripts/run_tests.sh`
  - `cd f-spa && npm test -- --run`
- Manual checks:
  - Validate completed upload status includes `results.faceCount`.
  - Validate submit status view shows green summary with large face count.
  - Validate Home/Activity rows show completed face-count and green success styling.
- Output summary:
  - `MS3` unit tests passed (`12/12`).
  - `f-spa` tests passed (`19/19`).

## Change Log

- `2026-04-16` - Initial task file created for phase-1 MS3 extraction + SPA face-count summary.
- `2026-04-16` - Implemented phase-1 MS3 extraction worker, queue wiring, and SPA completed face-count summary with passing tests.
- `2026-04-16` - Extended SPA to show completed face-count highlighting in Home/Activity feed rows.
