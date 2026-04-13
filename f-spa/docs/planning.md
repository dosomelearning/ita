# f-spa Implementation Plan

## Goal

Implement a complete, mobile-friendly SPA for shared-password entry, photo capture/submission, and ranking observation, while intentionally deferring concrete backend endpoint wiring.

## MVP Requirement

- Selecting an existing photo from device/computer is mandatory for MVP.
- Camera capture and existing-photo selection must both be first-class entry paths to the same submit pipeline.

## Today Definition of Done

- User can capture a photo from camera and proceed through submit flow.
- User can select an existing photo from device/computer and proceed through submit flow.
- Submit action works end-to-end in frontend using mock adapters (no backend wiring).
- UX states are functional for this flow: idle, validating, submitting, success, and failure.
- Mobile usability baseline is met (touch-friendly controls, responsive layout, clear feedback).

## Progress Snapshot (2026-04-13)

Completed:

- Implemented Home, Submit, and Ranking screens in frontend.
- Implemented camera capture and existing-photo selection.
- Implemented mock submit lifecycle with progress and phase chips (`queued`, `processing`, `completed`, `failed`).
- Implemented ranking preview on Home and full Ranking screen with refresh.
- Added required `Nickname` + `Code` fields on one row (nickname first, wider).
- `Code` is visible text input (`maxLength=6`), not password-masked.
- Capture/select/retake/change/submit actions are blocked until both nickname and code are present.
- Added mock adapter seam (`AuthGateway`, `UploadGateway`, `StateGateway`) and kept backend wiring deferred.
- Added initial automated tests for mock adapters.

Remaining before backend wiring:

- Replace local view switching with router-based URL navigation if desired.
- Add stricter client-side file validation (size/type limits) and user-facing validation copy.
- Expand tests to cover component-level UI flows and input gating behavior.
- Finalize runtime configuration contract for backend endpoint wiring.

## Product Direction

- Keep landing as the main "home" surface.
- Use home to combine password entry and ranking preview.
- Keep capture/submission as a focused flow with strong feedback.
- Keep full ranking available as an expanded view (separate route or modal).

## Planned Views

### 1) Home (`/`)

Purpose:

- Primary entry point for class users.
- Session setup and quick access to main actions.

Content:

- Nickname input + shared code input on the same line.
- `Capture Photo` and `Choose Photo` actions.
- Ranking preview (top N rows).
- Lightweight current-session status indicator.

Behavior:

- Nickname and code are stored in in-memory app state (not URL).
- Code is plain visible text input limited to 6 characters.
- Capture/select actions are disabled until nickname and code are provided.
- Invalid password state shown with clear recovery copy.
- Ranking preview can refresh manually and on interval.

### 2) Capture & Submit (`/submit`)

Purpose:

- Select/capture a photo and submit it for processing.

Content:

- Camera/file picker input.
- Image preview.
- `Retake/Change` and `Submit` actions.
- Processing timeline/status component.

Behavior:

- Enforce client-side file guardrails (size/type) before submit.
- Surface clear async statuses: `uploading`, `queued`, `processing`, `completed`, `failed`.
- Provide retry path and direct return to home/ranking.

### 3) Ranking (`/ranking`)

Purpose:

- Show full ranking and result details.

Content:

- Full list/table/cards with sort and refresh controls.
- Last updated timestamp and data freshness indicator.

Behavior:

- Uses same ranking data source as home preview.
- Supports pull-to-refresh style interaction on mobile.

## Information Architecture

- App shell with mobile-first vertical layout.
- Bottom sticky action area for thumb-reachable primary actions.
- Route transitions kept minimal and fast.
- Error banners and status chips standardized across views.

## State Model (Frontend)

- `sessionState`
  - `nickname`, `password`, `isPasswordAccepted`, `lastAuthError`
- `uploadState`
  - `selectedFile`, `previewUrl`, `uploadProgress`, `submissionStatus`, `error`
- `jobState`
  - `jobId`, `status`, `resultSummary`, `resultFaces`, `lastUpdatedAt`
- `rankingState`
  - `items`, `isLoading`, `error`, `lastFetchedAt`

State management approach:

- Start with React context + reducer slices.
- Keep state transitions explicit and testable.
- Avoid introducing heavy state libraries unless complexity justifies it.

## Backend Wiring Strategy (Deferred but Planned)

Define adapter interfaces now, implement mock adapters first:

- `AuthGateway`
  - `initUploadSession(password): Promise<InitUploadResult>`
- `UploadGateway`
  - `uploadPhoto(uploadTarget, file, onProgress): Promise<void>`
- `StateGateway`
  - `getJobState(jobId): Promise<JobStateResult>`
  - `getRanking(): Promise<RankingResult>`

Implementation rule:

- UI and state layer depend only on interfaces.
- Environment-specific HTTP implementation will be added later without changing view logic.

## Component Plan

- `PasswordPanel`
- `PhotoPicker`
- `PhotoPreviewCard`
- `SubmitProgress`
- `ProcessingTimeline`
- `RankingPreview`
- `RankingList`
- `StatusBanner`
- `ErrorBanner`

## Error Handling Plan

Business categories:

- Invalid password/admission denied.
- Unsupported file or client-side validation failure.
- Upload transfer failure.
- Processing timeout or backend failure status.
- Ranking fetch failure.

UX response:

- Always show actionable next step.
- Avoid dead-end error states.
- Preserve entered password and selected photo when safe.

## Mobile UX Requirements

- Touch targets at least 44px height.
- One-column flow with high-contrast CTA buttons.
- Camera-first control placement.
- Keep key controls in thumb zone.
- Avoid long forms and nested navigation.

## Testing Plan

Unit:

- Mock gateway tests are implemented (`src/mockGateways.test.ts`).
- Reducer/state transition tests for session/upload/job/ranking are pending if reducer extraction is introduced.

Component:

- Password entry and validation feedback.
- Capture/preview/submit state transitions.
- Ranking preview and full ranking rendering.

Integration (with mocks):

- Happy path from home -> submit -> completed -> ranking update.
- Failure paths for invalid password, upload failure, processing failure.

## Delivery Phases

1. Phase 1: App shell, routing, design tokens, shared components skeleton.
2. Phase 2: Home + ranking preview with mock data.
3. Phase 3: Capture/submit flow and status timeline with mock adapters.
4. Phase 4: Full ranking view, refresh behavior, error handling polish.
5. Phase 5: Test suite expansion and accessibility/responsiveness hardening.
6. Phase 6: Backend HTTP adapters and runtime config wiring (deferred by current scope).

## Definition of Ready for Backend Wiring

- Frontend interfaces finalized and used everywhere.
- Mock adapters cover all view states.
- Runtime config contract defined (API base URLs and feature flags).
- Error model aligned with `MS1` and `MS4` contract definitions.
