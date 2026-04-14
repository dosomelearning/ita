# T-020: Create End-to-End Process Sequence Diagram

## Metadata

- Status: `in_progress`
- Created: `2026-04-14`
- Last Updated: `2026-04-14`
- Related Backlog Item: `T-020`
- Related Modules: `README.md`, `ARCHITECTURE.md`, `f-spa/README.md`, `docs/process/photo-upload-processing-sequence.md`, `img/ita-photo-flow-sequence.mmd`

## Context

The project needs a single explicit process sequence view that matches documented architecture constraints, ownership boundaries, and runtime interaction order across frontend, ingress, processing, and state services.

## Scope

In scope:

- Create a verbal process description with ordered runtime steps.
- Create a sequence diagram source in `img/`.
- Embed the sequence diagram in the new process document.

Out of scope:

- Changing runtime architecture decisions.
- Implementing backend endpoint wiring in frontend code.
- Updating deployment scripts or AWS resources.

## AD Dependencies

- `AD-003` - Queue-based async boundaries define `MS2`/`MS3` stage transitions and DLQ-aware flow posture.
- `AD-004` - Shared password validation must happen in `MS1` before protected flow actions.
- `AD-005` - Public APIs are assumed rate-limited at API Gateway in the interaction model.
- `AD-008` - Two API surfaces (`MS1` and `MS4`) are preserved as distinct responsibilities in sequence steps.
- `AD-010` - Mixed synchronous API calls and asynchronous queue workers drive the process model.
- `AD-011` - Password lookup is represented via SSM Parameter Store under `MS1`.
- `AD-012` - Face detection and bounding metadata are owned by `MS2` with Rekognition.
- `AD-013` - Face extraction is owned by `MS3` using detection coordinates.
- `AD-016` - Upload-init state registration in `MS4` happens synchronously from `MS1`.
- `AD-017` - Shared processing queues are treated as centralized infra contracts.

## Acceptance Criteria

- [ ] New process doc exists under `docs/process/` with ordered verbal sequence.
- [ ] Sequence diagram source exists in `img/`.
- [ ] Process doc embeds the created sequence diagram.

## Implementation Notes

The diagram is authored as Mermaid sequence syntax (`.mmd`) in `img/` to keep architecture assets version-controlled alongside other visuals and easy to update incrementally.

## Validation Evidence

- Command(s) run:
  - `cat README.md`
  - `cat f-spa/README.md`
  - `cat ARCHITECTURE.md`
- Manual checks:
  - Verified sequence ordering reflects current architecture decisions.
- Output summary:
  - Process doc and diagram source are created and linked.

## Change Log

- `2026-04-14` - Initial draft.
