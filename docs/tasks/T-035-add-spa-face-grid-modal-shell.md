# T-035 Add SPA Face-Grid Modal Shell

- Status: `in_progress`
- Related Backlog Item: `T-035`
- Owner Area: `f-spa`

## Goal

Make the successful extraction face-count UI in SPA clickable and open a modal dialog that renders an empty responsive matrix of face slots.

## Scope

- Replace static success face-count number with interactive trigger.
- Add modal dialog open/close behavior in submit and activity views.
- Render empty matrix slots sized to `40x40` pixels.
- Support up to `99` slots.
- Compute responsive columns:
  - Prefer near-square layout on larger screens (up to 10 columns).
  - On mobile, constrain columns from available width budget based on `(viewportWidth - 200)` and tile+gap sizing.

## Progress Notes

- Submit status face-count is clickable and opens the modal.
- Home activity preview and full activity page face-count values are clickable and open the same modal.
- Modal currently renders placeholder slots only; no face images are bound yet.

## Validation

- `npx eslint src/App.tsx`
- `npm test`

## Out of Scope

- Rendering real extracted face images.
- Wiring modal slots to MS3 image URLs.

## AD Dependencies

- None.
