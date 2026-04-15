# T-030: Design Activity Feed Contract and MS4 Session Events Index

## Metadata

- Status: `in_progress`
- Created: `2026-04-15`
- Last Updated: `2026-04-15`
- Related Backlog Item: `T-030`
- Related Modules: `docs/tasks/T-010-define-frontend-backend-exchange-contracts.md`, `b-ms4-statemgr/README.md`, `b-ms4-statemgr/template.yaml`, `b-ms4-statemgr/src/api.py`, `b-ms4-statemgr/src/service.py`, `b-ms4-statemgr/src/repository.py`, `f-spa/src/App.tsx`, `f-spa/src/stateGateway.ts`

## Context

The project direction shifts from ranking-first UX to activity-first UX. SPA should show latest session activities (target: last 20), where each upload can contribute multiple pipeline events. Existing `MS4` data model stores event history per upload but does not currently expose efficient session-wide latest-events query without scan.

## Scope

In scope:

- Define business contract for session activity feed endpoint.
- Define DynamoDB no-scan query path for latest session events.
- Define `GSI3` key shape for activity feed ordering.
- Define frontend-facing activity payload and outcome marker semantics.

Out of scope:

- Full implementation in `MS4`/SPA.
- Decommissioning existing participant-history endpoint.

## AD Dependencies

- `AD-008` - `MS4` remains frontend read API owner for state/read model.
- `AD-010` - Activity feed reflects asynchronous pipeline stage events.
- `AD-016` - `MS4` remains authoritative workflow state/event projection source.
- `AD-017` - Queue-driven cross-service behavior remains unchanged.

## Contract Decision (Proposed)

### Endpoint

- `GET /v1/sessions/{sessionId}/activities`
- Query params:
  - `limit` (optional, default `20`, max `50`)
  - `before` (optional cursor token for pagination, future-ready)

### Response Shape

```json
{
  "sessionId": "session-a",
  "items": [
    {
      "uploadId": "upl-1234",
      "nickname": "ava",
      "participantId": "ava",
      "eventType": "detection_completed",
      "statusAfter": "processing",
      "eventTime": "2026-04-15T19:20:00Z",
      "producer": "ms2",
      "outcome": "in_progress",
      "details": {}
    }
  ]
}
```

### Outcome Mapping (UI Marker Intent)

- `statusAfter=completed` -> `outcome=success` (green check)
- `statusAfter=failed` -> `outcome=failure` (red X)
- `statusAfter=processing` -> `outcome=in_progress`
- `statusAfter=queued` (if emitted as event later) -> `outcome=queued`

### Include-All vs Aggregate

Decision:

- Display all events as feed entries (no aggregation in first iteration).
- Rationale:
  - More dynamic content and clearer pipeline trace.
  - Avoids premature aggregation logic and edge-case semantics.

## DynamoDB Query Model (No-Scan)

### `GSI3` Design

- `gsi3pk = FEED#CLASS#{classRunId}`
- `gsi3sk = E#{eventTimeMs}#U#{uploadId}#T#{eventType}`

Query pattern:

- `Query` on `GSI3` where `gsi3pk = FEED#CLASS#{classRunId}`
- `ScanIndexForward=false`
- `Limit=20`

Notes:

- `eventTimeMs` must be normalized ISO-8601 UTC with milliseconds (`YYYY-MM-DDTHH:MM:SS.SSSZ`) for lexical ordering.
- `classRunId` groups all concurrent users of the same class run (derived from class code in ingress flow; do not expose raw secret directly in feed identifiers).
- `T#{eventType}` prevents key collisions when multiple event types occur at same upload/time.

## Write-Path Impact

- On every `EVENT` item write, persist `gsi3pk`/`gsi3sk`.
- Optional future enhancement: emit explicit init event from `MS1` registration path for feed completeness.

## Acceptance Criteria

- [x] Activity feed endpoint contract drafted.
- [x] `GSI3` PK/SK proposal documented with ordering rationale.
- [x] No-scan query approach defined for latest N activities.
- [x] Outcome mapping for SPA visual markers documented.
- [x] Contract integrated into implementation tasks for `MS4` and SPA.

## Validation Evidence

- Command(s) run:
  - `cat docs/tasks/T-010-define-frontend-backend-exchange-contracts.md`
  - `cat b-ms4-statemgr/README.md`
  - `cat b-ms4-statemgr/src/repository.py`
  - `./scripts/test_local.sh`
- Manual checks:
  - Confirmed existing model lacks session-wide latest-event index path.
- Output summary:
  - Activity feed contract and finalized `GSI3` strategy (`FEED#CLASS` + `E/U/T` key format) documented.
  - `MS4` activity endpoint/index path and SPA activity feed integration implemented with passing local tests.

## Change Log

- `2026-04-15` - Initial contract/index design draft created.
- `2026-04-15` - Finalized compact `GSI3` key format and integrated implementation into `MS4` and SPA.
