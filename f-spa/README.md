# f-spa

Frontend single-page application (React + TypeScript), optimized for mobile upload flow.

## Related Docs

- [`../README.md`](../README.md) (project overview and boundaries)
- [`../AGENTS.md`](../AGENTS.md) (project workflow and guardrails)
- [`../b-infra/README.md`](../b-infra/README.md)
- [`../b-ms1-ingress/README.md`](../b-ms1-ingress/README.md)
- [`../b-ms2-detection/README.md`](../b-ms2-detection/README.md)
- [`../b-ms3-faces/README.md`](../b-ms3-faces/README.md)
- [`../b-ms4-statemgr/README.md`](../b-ms4-statemgr/README.md)

## Purpose

`f-spa` provides the user experience for photo capture/upload, job tracking, and displaying extracted face results.

## Responsibilities

- Capture/select photo on mobile-first UI.
- Submit shared password and request upload initialization from ingress API.
- Upload photo to presigned S3 URL returned by ingress.
- Poll/read processing state and result metadata via state API.
- Render extracted face images and related metadata.
- Optionally render class-oriented ranking/leaderboard views.

## External Interfaces

- `b-ms1-ingress` API:
  - Request presigned upload URL after password validation.
- `b-ms4-statemgr` API:
  - Query upload/detection/extraction status and fetch result references.
- `b-infra` shared platform outputs:
  - CloudFront/hosted domain entry point and related environment configuration.

## UX Requirements

- Primary flows must work well on mobile browsers.
- Clear feedback for async states: `queued`, `processing`, `completed`, `failed`.
- Fail fast and explain user-actionable recovery on invalid password or upload errors.

## Commands

- Install: `TBD (document once module tooling is scaffolded)`
- Test: `TBD`
- Lint: `TBD`
- Run: `TBD`

## Open Decisions

- Routing structure and state-management approach.
- Media capture constraints (file size/type/compression).
- Polling cadence and frontend caching strategy.
- Runtime configuration contract for consuming per-environment backend API endpoints.
