# T-022: Wire f-spa Status Polling to MS4

## Metadata

- Status: `in_progress`
- Created: `2026-04-14`
- Last Updated: `2026-04-14`
- Related Backlog Item: `T-022`
- Related Modules: `f-spa/src/App.tsx`, `f-spa/src/stateGateway.ts`, `f-spa/src/mockGateways.ts`, `f-spa/src/stateGateway.test.ts`, `f-spa/src/mockGateways.test.ts`, `f-spa/README.md`

## Context

`MS4` now provides status API contract (`GET /v1/uploads/{uploadId}/status`). SPA currently uses fully mock state progression and needs runtime-selectable wiring to read real status from `MS4`.

## Scope

In scope:

- Add SPA gateway implementation for `MS4` status polling.
- Keep mock gateway mode available.
- Use runtime config to switch mode without code changes.
- Update tests and docs for new behavior.

Out of scope:

- Full live backend wiring for `MS1` upload-init in SPA.
- Ranking endpoint integration (still mock unless separately implemented).

## AD Dependencies

- `AD-008` - SPA status reads should align with service-owned `MS4` API surface.
- `AD-016` - `MS4` is authoritative state source for upload lifecycle.

## Acceptance Criteria

- [x] SPA can poll `MS4` status API when runtime mode enables it.
- [x] SPA still supports pure mock mode for local/dev.
- [x] Status mapping handles `queued|processing|completed|failed`.
- [x] Unit tests cover mode selection and polling behavior.
- [x] `f-spa/README.md` documents required runtime env vars.

## Implementation Notes

Use adapter seam: keep upload/auth flow unchanged for this task, replace only state progression source with an environment-driven gateway strategy.

## Validation Evidence

- Command(s) run:
  - `npm test`
  - `npm run build`
- Manual checks:
  - Verified submit flow behavior in mock mode remains intact.
  - Verified MS4 mode polling logic and terminal-state mapping via unit tests.
- Output summary:
  - `f-spa` test suite passed (`10` tests).
  - `f-spa` production build completed successfully.
  - SPA status gateway can run in `mock` or `ms4` polling mode.

## Change Log

- `2026-04-14` - Initial draft.
