# T-032: Add README App Screenshots Section

## Metadata

- Status: `in_progress`
- Created: `2026-04-16`
- Last Updated: `2026-04-16`
- Related Backlog Item: `T-032`
- Related Modules: `README.md`, `img/app_screenshots/01-session-entry.png`, `img/app_screenshots/02-capture-and-submit.png`, `img/app_screenshots/03-activity.png`

## Context

The root project documentation should include a direct visual walkthrough of the SPA runtime UX.
Three screenshots are available and already capture the flow stages with annotations.

## Scope

In scope:

- Add a dedicated screenshots section in root `README.md`.
- Embed all three images from `img/app_screenshots/`.
- Add concise descriptions for each screen and call out notable UI states.

Out of scope:

- UI implementation changes in `f-spa`.
- Any backend contract or infrastructure modifications.

## Acceptance Criteria

- [x] Root `README.md` includes a new screenshots section.
- [x] All three screenshots are embedded and render by relative path.
- [x] Each screenshot has short explanatory notes covering observed flow/state.

## Validation Evidence

- Manual checks:
  - Open `README.md` and confirm image markdown paths resolve.
  - Confirm descriptions match screenshot content (`Session Entry`, `Capture and Submit`, `Activity Feed`).

## Change Log

- `2026-04-16` - Created task file and documented README screenshot-section scope and completion criteria.
