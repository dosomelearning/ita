# T-010: Define Frontend/Backend Exchange Contracts (MS1 + MS4)

## Metadata

- Status: `todo`
- Created: `2026-03-08`
- Last Updated: `2026-03-08`
- Related Backlog Item: `T-010`
- Related Modules: `f-spa`, `b-ms1-ingress`, `b-ms4-statemgr`, `docs/system-checklist.md`

## Context

The architecture has two frontend contact points:

- `MS1` (`b-ms1-ingress`) for presigned upload URL preparation.
- `MS4` (`b-ms4-statemgr`) for workflow state and result retrieval.

To avoid integration ambiguity, business-level communication patterns must be defined before detailed implementation.

## Scope

In scope:

- Define business-level request/response patterns between frontend and backend.
- Define frontend interactions with `MS1` for upload initialization and admission outcomes.
- Define frontend interactions with `MS4` for state polling/reading and result retrieval.
- Define business-level error categories and expected frontend behavior per category.
- Define correlation and state-tracking expectations across frontend-visible flows.

Out of scope:

- Detailed low-level payload schema for internal microservice-to-microservice messages.
- Full implementation of APIs.
- UI implementation specifics.

## Acceptance Criteria

- [ ] A clear business interaction map exists for frontend <-> `MS1` and frontend <-> `MS4`.
- [ ] Required frontend request intents and backend response intents are documented.
- [ ] Error/edge scenarios are documented at business-contract level.
- [ ] Contract descriptions are consistent with async processing model and queue-based backend flow.
- [ ] Module READMEs are updated or linked so contract ownership is discoverable.

## Implementation Notes

- Keep contracts business-oriented first: what user flow step is requested and what outcome/status is returned.
- Keep `MS1` scope narrow: admission + presigned URL initiation only.
- Keep `MS4` scope explicit: workflow status/results read model for frontend.
- Ensure terms are consistent across root and module documentation.

## Validation Evidence

- Command(s) run:
  - `sed -n '1,260p' docs/system-checklist.md`
- Manual checks:
  - Confirmed `T-010` backlog item exists and links this task file.
- Output summary:
  - Backlog and detailed task entry created.

## Change Log

- `2026-03-08` - Initial draft.
