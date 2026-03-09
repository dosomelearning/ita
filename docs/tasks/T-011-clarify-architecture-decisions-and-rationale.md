# T-011: Clarify Architecture Decisions and Rationale

## Metadata

- Status: `in_progress`
- Created: `2026-03-09`
- Last Updated: `2026-03-09`
- Related Backlog Item: `T-011`
- Related Modules: `README.md`, `ARCHITECTURE.md`, `docs/README.md`, `b-infra`, `b-ms1-ingress`, `b-ms2-detection`, `b-ms3-faces`, `b-ms4-statemgr`, `f-spa`

## Context

Current documentation explains architecture direction, but key design decisions and tradeoffs need clearer, explicit rationale to reduce ambiguity during implementation.

## Scope

In scope:

- Define where architectural decision rationale should live.
- Capture explicit reasoning for documentation structure decisions.
- Create an architecture decision document that complements root `README.md`.
- Ensure task tracking references include the new decision artifact.

Out of scope:

- Changing service boundaries or core architecture direction.
- Implementing backend/frontend runtime features.
- Marking task `T-011` as `done` (requires explicit user instruction).

## AD Dependencies

- `AD-001`: Defines the documentation split (`README.md` overview vs `ARCHITECTURE.md` decision rationale) that this task operationalizes.
- `AD-002`: Provides service/shared ownership baseline that must remain consistent across architecture rationale updates.
- `AD-003` to `AD-021`: This task is the source task for documenting and maintaining these architecture decisions coherently in `ARCHITECTURE.md`.

## Questions Discussed and Reasoning

1. Should we explain architectural decisions directly in `README.md` or create a dedicated file?
   - Decision: Use both with clear responsibilities.
   - Reasoning:
     - Keep `README.md` as concise architecture overview and entrypoint.
     - Use `ARCHITECTURE.md` for deeper rationale, alternatives, and tradeoffs.
     - This improves readability while preserving decision history.

2. Where should `ARCHITECTURE.md` be located: project root or `docs/`?
   - Decision: Place `ARCHITECTURE.md` in project root.
   - Reasoning:
     - Root `README.md` is the required architecture entrypoint and working map start.
     - Root placement improves discoverability and keeps architecture context top-level.
     - `docs/` remains primarily focused on operational process and task tracking.

## Acceptance Criteria

- [x] `T-011` backlog item moved to `in_progress`.
- [x] Root-level `ARCHITECTURE.md` created with initial decision rationale.
- [x] This task file records discussed questions and reasoning.
- [x] `docs/system-checklist.md` links include `ARCHITECTURE.md` and this task file.
- [x] Root `README.md` cross-links to `ARCHITECTURE.md`.
- [ ] Module/docs links are adjusted as needed to keep documentation map coherent.

## Implementation Notes

- Initial architecture decision captured as `AD-001` in `ARCHITECTURE.md`.
- Follow-up updates should keep root overview concise and move deeper decision details into this dedicated file.
- Workflow rule:
  - `ARCHITECTURE.md` is the canonical and complete source of architectural decisions (all `AD-###` entries).
  - This `T-011` task file may list only currently planned/in-progress topics and must not duplicate the full AD catalog.
- Planned decision topics to author under `ARCHITECTURE.md` during `T-011`:
  - Shared infra vs service-owned resource boundaries.
  - Why queue-based async boundaries are mandatory in this demo.
  - Shared password flow and rejection boundary in `MS1`.
  - API Gateway rate limiting as mandatory control.
  - Data-lifecycle constraints for classroom/EU context.
  - Git workflow decision for current phase (`main`-only, with future option to adopt PR/CI branching model).

## Validation Evidence

- Command(s) run:
  - `sed -n '1,220p' docs/tasks/TEMPLATE.md`
  - `ls -1 docs/tasks | sort`
  - `sed -n '1,240p' docs/tasks/T-010-define-frontend-backend-exchange-contracts.md`
  - `rg -n "T-011|ARCHITECTURE.md|T-011-clarify-architecture-decisions-and-rationale.md" docs/system-checklist.md ARCHITECTURE.md docs/tasks/T-011-clarify-architecture-decisions-and-rationale.md`
- Manual checks:
  - Confirmed `T-011` status is `in_progress`.
  - Confirmed new architecture document and task detail file exist.
- Output summary:
  - Task tracking and architecture-document baseline for `T-011` established.

## Change Log

- `2026-03-09` - Initial task detail file created with agreed questions and reasoning.
