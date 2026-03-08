# Temporary Session Handoff - 4-ita

Date: 2026-03-08

## What Was Completed In This Session

- Confirmed project root and active working path: `/home/raven/data/sc/uni/4-ita`.
- Read/validated architecture direction from:
  - `img/ita-arch-diag1.png`
  - root `README.md`
  - project `AGENTS.md`
- Created starter module documentation files:
  - `b-infra/README.md`
  - `b-ms1-ingress/README.md`
  - `b-ms2-detection/README.md`
  - `b-ms3-faces/README.md`
  - `b-ms4-statemgr/README.md`
  - `f-spa/README.md`
- Updated root `README.md`:
  - Added explicit ownership/isolation model.
  - Added explicit "diagram vs ownership" section.
  - Moved `Working Map` section directly under architecture diagram.
  - Converted module README paths in working map to clickable links.
  - Added visible note that links are clickable in markdown-capable viewers.
- Updated project `AGENTS.md` with ownership/isolation rules:
  - `b-infra` is shared/foundational only.
  - Each backend microservice owns its own SAM template/resources.
  - Monorepo does not reduce service autonomy.
- Initialized git repository at project root and configured remote:
  - `origin` -> `https://github.com/dosomelearning/ita.git`

## Key Decisions Captured (Do Not Re-discuss Unless Needed)

- Canonical directories are locked:
  - `b-infra`
  - `b-ms1-ingress`
  - `b-ms2-detection`
  - `b-ms3-faces`
  - `b-ms4-statemgr`
  - `f-spa`
  - `img`
- Global `~/.codex/AGENTS.md` rules are valid; project `AGENTS.md` adds project-specific constraints.
- Agent shell behavior:
  - Never use login shell.
  - Show exact shell command before execution.
- Allowed paths without asking user:
  - project path (`/home/raven/data/sc/uni/4-ita`)
  - `~/.codex`
- Any access outside those paths requires explicit user approval first.
- Python runtime for agent commands is fixed:
  - `conda run -n conda_py_env_312 ...`
- `.idea/` is user-owned and must not be edited unless explicitly requested.
- Ownership model is now explicit:
  - `b-infra` owns foundational/shared platform resources only (e.g., CloudFront, hosting S3, Route53, ACM, shared buckets, baseline logging/observability).
  - Each backend microservice (`b-ms1-ingress`, `b-ms2-detection`, `b-ms3-faces`, `b-ms4-statemgr`) owns its own SAM template and service-owned resources.
  - Cross-service dependencies must be via explicit contracts (API/events/storage contracts), not implicit coupling.
- Canonical repository URL:
  - `https://github.com/dosomelearning/ita` (git remote URL uses `.git` suffix)
- Git push ownership:
  - User pushes to remote repositories exclusively.
  - Agent performs local git operations/commits only with explicit user approval.

## Architecture / Product Direction

- Demo app for resilient AWS serverless architecture.
- Mobile-first SPA captures photos and uploads them.
- Backend pipeline detects faces (Rekognition), extracts individual face images, and serves them back to frontend.
- Classroom usage: concurrent users; potential leaderboard scenarios (e.g., photo with most faces).
- No Cognito.
- Shared one-time password flow via DynamoDB:
  - instructor defines password
  - ingress issues presigned URL only on valid password
  - invalid password requests are rejected before protected flow
- All API Gateway endpoints must be rate-limited.

## AWS Guardrails

- Default CLI settings to enforce when AWS commands are used:
  - `--profile dev`
  - region `eu-central-1`
  - `AWS_CLI_AUTO_PROMPT=off`
  - `AWS_PAGER=""`
  - `AWS_EC2_METADATA_DISABLED=true`
  - `--no-cli-pager`
- No AWS write/create/update/delete actions without explicit per-command user approval.
- Never run `sam deploy` without explicit approval.

## Current Documentation State

- Root docs:
  - `AGENTS.md` tailored and active, including ownership/isolation rules.
  - `README.md` now includes:
    - architecture image
    - working map near top with clickable module links
    - access model
    - repository layout
    - ownership/isolation model
    - diagram-vs-ownership clarification
    - technology baseline, status, and milestones
- Module docs:
  - All six module `README.md` files exist with starter content:
    - purpose
    - responsibilities
    - inbound/outbound interface notes
    - constraints/open decisions
    - placeholder command sections (`install`/`test`/`lint`/`run` as `TBD`)

## Immediate Next Step When User Returns

1. Define explicit cross-stack/service contract details in module READMEs:
   - Required `b-infra` outputs consumed by each service.
   - Service-owned outputs produced for other modules/frontend.
2. Scaffold initial SAM templates for:
   - `b-infra` (foundational/shared resources only)
   - each backend microservice (autonomous service-owned resources only)
3. Decide and document ownership of ambiguous resources (especially shared queues/tables) before implementation.
4. Start defining concrete module commands (`install`/`test`/`lint`/`run`) once scaffolds/tooling exist.
5. Keep doc-first alignment with `img/ita-arch-diag1.png` and stop if diagram/docs diverge materially.

## Resume Prompt (Copy/Paste)

"Continue from `TEMP_SESSION_HANDOFF.md` in `/home/raven/data/sc/uni/4-ita`, keep microservice ownership isolation strict (shared in `b-infra`, service-owned in each `b-ms*` SAM template), and proceed with cross-stack contracts plus initial SAM scaffolding."
