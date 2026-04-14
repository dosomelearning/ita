# T-026: Add MS4 Participant History Query Model

## Metadata

- Status: `in_progress`
- Created: `2026-04-14`
- Last Updated: `2026-04-14`
- Related Backlog Item: `T-026`
- Related Modules: `b-ms4-statemgr/src/domain.py`, `b-ms4-statemgr/src/service.py`, `b-ms4-statemgr/src/repository.py`, `b-ms4-statemgr/src/api.py`, `b-ms4-statemgr/template.yaml`, `b-ms4-statemgr/tests/unit/*`, `b-ms4-statemgr/README.md`

## Context

Current `MS4` reads are upload-centric (`GET /v1/uploads/{uploadId}/status`). We need participant-oriented reads for user history and future ranking features, while preserving the no-`Scan` DynamoDB rule.

## Scope

In scope:

- Persist participant identity fields (`nickname`, canonical participant key) in state item at init.
- Add DynamoDB `GSI2` for participant history queries.
- Add public read endpoint for participant upload history.
- Keep all retrieval paths on `GetItem`/`Query` only.
- Update tests and service docs.

Out of scope:

- Full ranking aggregation endpoint.
- Changes to `MS2`/`MS3` processing logic.

## Acceptance Criteria

- [x] Init payload includes participant identity and stores it in state.
- [x] Table has a participant-oriented query index (`GSI2`) and is queried (no scan).
- [x] `GET /v1/sessions/{sessionId}/participants/{nickname}/uploads` returns participant upload history.
- [x] Unit tests cover validation, routing, service behavior, and repository query path.
- [x] `b-ms4-statemgr/README.md` documents new contract and route.

## AD Dependencies

- `AD-001`: Service-owned resources remain in microservice template.
- `AD-002`: Internal routes stay IAM-protected; public read route remains under `/v1`.
- `AD-003`: Async pipeline remains event-driven; this task only improves state/read model.
- `AD-004`: No direct service coupling beyond documented contracts.

## Validation Evidence

- Command(s) run:
  - `cd b-ms4-statemgr && ./scripts/run_tests.sh`
  - `cd b-ms4-statemgr && sam validate --template-file template.yaml`
- Output summary:
  - Added participant identity to init contract and persisted fields in state item.
  - Added `GSI2` model/query path for participant history without DynamoDB scans.
  - Added participant history route in `MS4` API and unit tests for route/service/repository behavior.
