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
Current implementation includes frontend-only flow with mock adapters:

- shared code/password entry
- photo capture from camera
- selecting an existing photo from device/computer
- mock submit lifecycle with upload/progress/status states
- activity feed preview and full activity screen (mock or MS4-backed)
- runtime-selectable state gateway:
  - `mock` mode for local/dev flow
  - `ms4` mode for live status polling via `GET /v1/uploads/{uploadId}/status`

## Responsibilities

- Capture/select photo on mobile-first UI.
- Submit shared password and request upload initialization from ingress API.
- Upload photo to presigned S3 URL returned by ingress.
- Poll/read processing state and result metadata via state API.
- Render extracted face images and related metadata.
- Render class-wide latest activity feed entries (`latest 20` default).

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

- Install: `npm install`
- Test: `npm test`
- Lint: `npm run lint`
- Run: `npm run dev`
- Build: `npm run build`
- Deploy to S3 web bucket: `./scripts/deploy_spa.sh`
- Optional deploy overrides: `WEB_BUCKET`, `DISTRIBUTION_ID`, `INFRA_STACK_NAME`, `AWS_PROFILE`, `AWS_REGION`

## Open Decisions

- Routing structure and state-management approach.
- Media capture constraints (file size/type/compression).
- Polling cadence and frontend caching strategy.
- Runtime configuration contract for consuming per-environment backend API endpoints.

## Runtime Config (Status Gateway)

Environment variables (Vite):

- `VITE_INGRESS_GATEWAY_MODE`:
  - `mock` (default) -> mock upload-init + mock upload transport.
  - `ms1` -> call `MS1` upload-init endpoint and upload to returned presigned URL.
- `VITE_MS1_API_BASE_URL`:
  - Required when `VITE_INGRESS_GATEWAY_MODE=ms1`.
  - Example: `https://si01n8xiyc.execute-api.eu-central-1.amazonaws.com`

- `VITE_STATE_GATEWAY_MODE`:
  - `mock` (default) -> fully mocked state progression.
  - `ms4` -> poll `MS4` status endpoint for submit lifecycle status.
- `VITE_MS4_API_BASE_URL`:
  - Required when `VITE_STATE_GATEWAY_MODE=ms4`.
  - Example: `https://ita.dosomelearning.com`
- Starter file: copy values from `.env.example`.

Current scope note:

- Activity feed is class-run scoped and uses `MS1`-returned `classRunId` in `ms4` mode.
