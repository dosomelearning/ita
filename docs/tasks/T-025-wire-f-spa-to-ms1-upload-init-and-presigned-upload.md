# T-025: Wire f-spa to MS1 Upload-Init and Presigned Upload

## Metadata

- Status: `in_progress`
- Created: `2026-04-14`
- Last Updated: `2026-04-14`
- Related Backlog Item: `T-025`
- Related Modules: `f-spa/src/App.tsx`, `f-spa/src/ingressGateway.ts`, `f-spa/src/ingressGateway.test.ts`, `f-spa/src/mockGateways.ts`, `f-spa/.env.example`, `f-spa/README.md`, `b-infra/template-infra.yaml`

## Context

SPA status polling to `MS4` is already wired. Submit flow still uses mock init/upload behavior, so real S3 uploads are not occurring. This task wires SPA to `MS1` upload-init and real presigned URL upload path.

## Scope

In scope:

- Add runtime-selectable ingress gateway mode (`mock`/`ms1`).
- Implement `MS1` upload-init HTTP adapter in SPA.
- Implement browser upload via presigned `PUT` URL.
- Keep mock fallback mode for local development.
- Update docs and env examples.

Out of scope:

- Ranking endpoint backend wiring.
- Replace `MS4` state polling mode behavior.

## Acceptance Criteria

- [x] SPA can call `MS1 /v1/uploads/init` and obtain real `uploadId` + presigned URL.
- [x] SPA can upload selected file to presigned URL.
- [x] Existing mock mode remains functional.
- [x] Unit tests cover gateway mode selection and key request/response behavior.
- [x] Runtime env docs include `MS1` gateway settings.

## Validation Evidence

- Command(s) run:
  - `cd f-spa && npm test`
  - `cd f-spa && npm run build`
- Manual checks:
  - Verify gateway debug labels reflect selected ingress/state/upload modes.
- Output summary:
  - `ingressGateway` added with runtime mode switch (`mock`/`ms1`).
  - `App.tsx` submit flow now performs real `MS1` init and presigned S3 upload in `ms1` mode.
  - Added explicit error hint for upload `status=0` (`network/CORS`).
  - Confirmed live issue root cause: missing CORS config on shared processing bucket.
  - Added CORS rules on shared processing bucket (`localhost:5173`, `127.0.0.1:5173`, `https://ita.dosomelearning.com`; methods `PUT/GET/HEAD`; headers `*`).
  - SPA test suite passed (`16` tests) and production build succeeded.

## Change Log

- `2026-04-14` - Initial draft.
