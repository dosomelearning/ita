# T-027: Centralize Testing and Diagnostics Strategy

## Metadata

- Status: `in_progress`
- Created: `2026-04-15`
- Last Updated: `2026-04-15`
- Related Backlog Item: `T-027`
- Related Modules: `README.md`, `docs/README.md`, `docs/testing/README.md`, `scripts/README.md`, `scripts/test_local.sh`, `scripts/test_live_basic.sh`, `scripts/test_live_e2e.sh`, `scripts/smoke_check.sh`, `scripts/test_all.sh`

## Context

Tests exist per module but are not yet presented as one centralized, visible project workflow. Diagnostics scripts also exist (`scripts/describe_ita_*`) and should be documented alongside testing to give one operational source of truth for "what is validated" and "how to inspect deployed state".

## Scope

In scope:

- Create one central testing+diagnostics strategy document.
- Link this document from root `README.md` and docs map.
- Add centralized root-level runner scripts for local checks, live-basic checks, optional live e2e smoke, and combined orchestration.
- Standardize summary output and write a machine-readable JSON report artifact for each run.

Out of scope:

- CI pipeline setup.
- New module test implementations.
- AWS write operations.

## AD Dependencies

- `AD-001` - Documentation split follows project-level architecture/docs structure.
- `AD-015` - Operational visibility alignment: test/diagnostics entry points stay explicit and consistent.
- `AD-018` - IaC-only operation support includes repeatable verification and read-only diagnostics routines.

## Acceptance Criteria

- [x] Central testing strategy document exists under `docs/testing/`.
- [x] Root `README.md` and `docs/README.md` link to centralized testing docs.
- [x] Root scripts provide centralized runs for local checks and live smoke checks.
- [x] Existing diagnostics scripts are documented under a dedicated diagnostics section in the same source of truth.
- [x] Script runs emit both terminal summary and JSON report artifact path.

## Implementation Notes

- `local` tier is deterministic and network-independent.
- `live-basic` tier validates public API envelopes without requiring a valid class password.
- `live-e2e` tier is optional and requires `SMOKE_CLASS_PASSWORD`; until `MS2`/`MS3` are implemented, `queued` is an expected terminal observation.

## Validation Evidence

- Command(s) run:
  - `./scripts/test_local.sh`
  - `./scripts/smoke_check.sh --tier live-basic` (requires networked runtime)
- Manual checks:
  - Verified root/docs links point to central strategy doc.
  - Verified diagnostics scripts are listed under diagnostics section.
- Output summary:
  - Centralized testing+diagnostics strategy now visible from root docs.
  - Standardized root scripts now provide unified entrypoints and JSON report output.
  - Added central endpoint configuration source via `scripts/testing.env` with optional local overrides.

## Change Log

- `2026-04-15` - Initial draft.
