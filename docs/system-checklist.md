# System Checklist

Use this file as the live project backlog for cross-service, architecture, security, and delivery work.

Last Issued ID: `T-009`

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

## Active Items

| ID | Status | Area | Task | Links | Notes |
|---|---|---|---|---|---|
| T-003 | todo | Infra | Set up `b-infra` as the first project stack with shared platform resources defined in its CloudFormation template. | `b-infra/README.md`, `docs/tasks/T-003-setup-b-infra-shared-stack.md` | Planned; single processing bucket + prefix layout, S3->SQS upload notification, SNS for system alarms |
| T-004 | todo | Frontend | Set up initial frontend scaffolding in existing `f-spa` module. | `f-spa/README.md`, `docs/tasks/T-004-setup-f-spa-scaffolding.md` | Planned; scaffold only, no full feature implementation |
| T-005 | todo | Backend | Scaffold `b-ms1-ingress` with AWS SAM baseline template and module structure. | `b-ms1-ingress/README.md`, `docs/tasks/T-005-scaffold-b-ms1-ingress-with-sam.md` | Planned; scaffold only, contracts implemented later |
| T-006 | todo | Backend | Scaffold `b-ms2-detection` with AWS SAM baseline template and module structure. | `b-ms2-detection/README.md`, `docs/tasks/T-006-scaffold-b-ms2-detection-with-sam.md` | Planned; scaffold only, Rekognition flow implemented later |
| T-007 | todo | Backend | Scaffold `b-ms3-faces` with AWS SAM baseline template and module structure. | `b-ms3-faces/README.md`, `docs/tasks/T-007-scaffold-b-ms3-faces-with-sam.md` | Planned; scaffold only, extraction logic implemented later |
| T-008 | todo | Backend | Scaffold `b-ms4-statemgr` with AWS SAM baseline template and module structure. | `b-ms4-statemgr/README.md`, `docs/tasks/T-008-scaffold-b-ms4-statemgr-with-sam.md` | Planned; scaffold only, state API logic implemented later |
