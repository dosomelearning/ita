# T-033: Harden SPA and MS1 Input Validation

## Metadata

- Status: `in_progress`
- Created: `2026-04-16`
- Last Updated: `2026-04-16`
- Related Backlog Item: `T-033`
- Related Modules: `f-spa/src/App.tsx`, `f-spa/src/inputValidation.ts`, `f-spa/src/inputValidation.test.ts`, `f-spa/src/mockGateways.ts`, `f-spa/src/mockGateways.test.ts`, `b-ms1-ingress/src/domain.py`, `b-ms1-ingress/tests/unit/test_domain.py`, `b-ms1-ingress/tests/unit/test_service.py`, `b-ms1-ingress/tests/unit/test_api.py`

## Context

Session-entry inputs are security- and correctness-sensitive because they are used for admission (`MS1`) and user identity labeling in activity/status views.
Validation currently allows malformed values to pass too far into the flow.

## Scope

In scope:

- Enforce shared class code constraints in frontend and backend:
  - No spaces.
  - Allow letters, numbers, and special characters.
- Enforce nickname constraints in frontend and backend:
  - No spaces.
  - Alphanumeric only.
  - Must start with a letter.
  - Maximum length 20 characters.
- Add/extend unit tests proving acceptance/rejection behavior.

Out of scope:

- Authentication model changes beyond existing shared-code flow.
- API contract redesign outside validation behavior.

## Acceptance Criteria

- [x] SPA prevents submission until nickname/code are valid under new rules.
- [x] `MS1` rejects invalid nickname/code payloads with `VALIDATION_ERROR`.
- [x] Unit tests cover new validation behavior in SPA and `MS1`.

## Validation Evidence

- Executed automated checks:
  - `cd f-spa && npm test` -> pass (`27` tests)
  - `cd b-ms1-ingress && ./scripts/run_tests.sh` -> pass (`16` tests)
- Executed live smoke checks after nickname alignment:
  - `./scripts/test_live_basic.sh` -> pass (`5/5`)
  - `./scripts/test_live_e2e.sh` -> pass (`4/4`)

## Change Log

- `2026-04-16` - Created task file for dual-layer input-validation hardening and unit test coverage.
- `2026-04-16` - Implemented SPA + MS1 validation rules; aligned smoke nickname defaults with strict nickname validation.
