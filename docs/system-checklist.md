# System Checklist

Use this file as the live project backlog for cross-service, architecture, security, and delivery work.

Last Issued ID: `T-019`

## Rules

- Keep each item short and outcome-focused.
- Use one status only: `todo`, `in_progress`, `blocked`, or `done`.
- Use single ID format: `T-###` (for example, `T-004`).
- When adding an item, increment from `Last Issued ID` and then update `Last Issued ID`.
- A task may transition to `done` only on explicit user instruction.
- Task-related commits must use commit intent tag in subject: `[checkpoint]` or `[close]`.
- `[checkpoint]` commits are allowed for `todo`, `in_progress`, or `blocked`; keep task in active backlog.
- `[close]` commits are allowed only for `done` tasks; remove closed task row in the same commit.
- Commit messages must reference related `T-###` IDs.
- Completion history is tracked in git log and commit messages.
- Create a detailed task file in `docs/tasks/` only when an item needs more than a short backlog row.
- When a detailed task file exists and architecture decisions apply, include an `AD Dependencies` section with related `AD-###` entries and short impact notes.
- In `## Active Items`, keep each task `ID` as a clickable markdown link to its detailed task file using a path relative to this file (for example `tasks/T-015-...md`).

## Active Items

| ID | Status | Area | Task | Links | Notes |
|---|---|---|---|---|---|
| [T-010](tasks/T-010-define-frontend-backend-exchange-contracts.md) | todo | Contracts | Define business-level frontend/backend communication patterns and exchange contracts via `MS1` and `MS4`. | `README.md`, `b-ms1-ingress/README.md`, `b-ms4-statemgr/README.md`, `tasks/T-010-define-frontend-backend-exchange-contracts.md` | Planned; focus on business exchange patterns, not implementation detail |
| [T-011](tasks/T-011-clarify-architecture-decisions-and-rationale.md) | in_progress | Architecture | Clarify architecture decisions and rationale across system documentation. | `README.md`, `ARCHITECTURE.md`, `docs/README.md`, `b-infra/README.md`, `b-ms1-ingress/README.md`, `b-ms2-detection/README.md`, `b-ms3-faces/README.md`, `b-ms4-statemgr/README.md`, `f-spa/README.md`, `tasks/T-011-clarify-architecture-decisions-and-rationale.md` | In progress; explain key decisions, boundaries, tradeoffs, and documentation placement rationale |
| [T-017](tasks/T-017-define-cross-service-queue-contracts-and-dlq-operations.md) | todo | Contracts | Define cross-service queue contract plan (payload schema, versioning, retry semantics, DLQ replay procedure) for shared boundary queues. | `b-infra/README.md`, `tasks/T-017-define-cross-service-queue-contracts-and-dlq-operations.md`, `tasks/T-003-setup-b-infra-shared-stack.md` | Planned; split from completed infra baseline setup |
| [T-019](tasks/T-019-plan-f-spa-complete-implementation.md) | in_progress | Frontend | Define complete SPA implementation plan (mobile UX, screen flow, state model, test strategy), while deferring concrete backend wiring. | `f-spa/README.md`, `f-spa/docs/planning.md`, `tasks/T-019-plan-f-spa-complete-implementation.md` | In progress; today target = capture/select photo and mock submit flow fully working |
