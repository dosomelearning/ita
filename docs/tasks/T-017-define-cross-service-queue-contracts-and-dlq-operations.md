# T-017: Define Cross-Service Queue Contracts and DLQ Operations

## Metadata

- Status: `todo`
- Created: `2026-03-09`
- Last Updated: `2026-03-09`
- Related Backlog Item: `T-017`
- Related Modules: `b-infra/README.md`, `docs/tasks/T-003-setup-b-infra-shared-stack.md`, `b-ms2-detection/README.md`, `b-ms3-faces/README.md`

## Context

`T-003` established shared infra resources (queues, DLQs, and wiring), but detailed queue contract definitions are intentionally split into dedicated follow-up work.

## Scope

In scope:

- Define payload contract plan for cross-service boundary queues.
- Define contract versioning strategy.
- Define retry semantics and failure taxonomy alignment with queue/DLQ behavior.
- Define DLQ replay procedure and operational safety notes.

Out of scope:

- Major infrastructure re-architecture.
- Service implementation rewrites.

## Acceptance Criteria

- [ ] Queue payload schema documentation plan exists for each boundary queue.
- [ ] Versioning approach is documented.
- [ ] Retry and error-handling semantics are documented.
- [ ] DLQ replay procedure is documented with safety constraints.
- [ ] Relevant module docs are updated/linked for discoverability.

## AD Dependencies

- `AD-003`: Async queue boundaries and DLQ handling are core to this task scope.
- `AD-017`: Queue/DLQ ownership is centralized in `b-infra`; this task defines contract/operations layer on top.
- `AD-020`: Alarm strategy depends on meaningful queue/DLQ semantics and replay procedures.

## Implementation Notes

- Keep resource ownership and contract ownership as separate concerns.
- Keep contract docs concise and operationally actionable.

## Validation Evidence

- Command(s) run:
  - `sed -n '1,220p' docs/tasks/T-003-setup-b-infra-shared-stack.md`
  - `sed -n '1,120p' docs/system-checklist.md`
- Manual checks:
  - Confirmed queue contract scope split from completed `T-003`.
- Output summary:
  - Follow-up task created for queue contract and DLQ operations planning.

## Change Log

- `2026-03-09` - Initial task file created as follow-up split from `T-003`.
