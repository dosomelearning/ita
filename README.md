# 4-ita

Serverless demo application for classroom-scale photo ingestion and face extraction on AWS.

## Repository

- Canonical GitHub repository: [https://github.com/dosomelearning/ita](https://github.com/dosomelearning/ita)

## Related Docs

- [`AGENTS.md`](AGENTS.md) (project working rules)
- [`TEMP_SESSION_HANDOFF.md`](TEMP_SESSION_HANDOFF.md) (latest session continuity notes)
- [`b-infra/README.md`](b-infra/README.md)
- [`b-ms1-ingress/README.md`](b-ms1-ingress/README.md)
- [`b-ms2-detection/README.md`](b-ms2-detection/README.md)
- [`b-ms3-faces/README.md`](b-ms3-faces/README.md)
- [`b-ms4-statemgr/README.md`](b-ms4-statemgr/README.md)
- [`f-spa/README.md`](f-spa/README.md)

## What This Project Is

`4-ita` is a learning/demo system that shows how to build a resilient, managed, serverless workflow for concurrent mobile users.
Students use a mobile-first SPA to capture/upload images, backend services process images with AWS managed services, and extracted face images are made available back to the frontend.

## Architecture Diagram

![4-ita architecture](img/ita-arch-diag1.png)

Source image: `img/ita-arch-diag1.png`.

## Working Map (Read This First)

Use this order to understand and continue the project:
Note: in markdown-capable viewers, the module `README.md` entries below are **clickable links**.

1. This root `README.md` for system intent and architecture direction.
2. Diagram(s) in `img/` for current architecture reference.
3. Module-level `README.md` files for implementation details:
   - [`b-infra/README.md`](b-infra/README.md)
   - [`b-ms1-ingress/README.md`](b-ms1-ingress/README.md)
   - [`b-ms2-detection/README.md`](b-ms2-detection/README.md)
   - [`b-ms3-faces/README.md`](b-ms3-faces/README.md)
   - [`b-ms4-statemgr/README.md`](b-ms4-statemgr/README.md)
   - [`f-spa/README.md`](f-spa/README.md)

If documentation and diagrams diverge, pause and reconcile before implementation.

## Core Goals

- Demonstrate AWS serverless/managed architecture under concurrent class usage.
- Accept photo uploads from mobile-first frontend flow.
- Detect faces with Amazon Rekognition.
- Extract each detected face into an individual image artifact.
- Return processed results for frontend consumption.
- Enable simple class-oriented ranking/leaderboard scenarios (for example, most faces detected in a photo).

## Access Model (Current Direction)

- No Cognito authentication in this project.
- Access is gated by a shared one-time password defined by instructor and stored in DynamoDB.
- Presigned upload URL issuance is allowed only when shared password validation succeeds.
- Requests with invalid password are rejected before entering protected processing flow.
- API Gateway endpoints must be rate-limited.

## Repository Layout

- `b-infra` - foundational/shared infrastructure (for example CloudFront, frontend hosting bucket, shared data buckets, Route53, ACM, baseline logging/observability).
- `b-ms1-ingress` - ingress microservice (request admission + presigned URL workflow).
- `b-ms2-detection` - detection microservice (face detection orchestration).
- `b-ms3-faces` - face extraction/storage microservice.
- `b-ms4-statemgr` - state/aggregation microservice (status, ranking, and flow state).
- `f-spa` - React + TypeScript single-page frontend (mobile-first UX).
- `img` - architecture and supporting diagrams.

Directory names above are canonical and intentionally locked.

## Ownership and Isolation Model

- This repository is a monorepo, but backend services remain isolated/autonomous units.
- `b-infra` contains only project-foundational/shared AWS resources.
- Each backend microservice owns its own SAM template and service-owned resources.
- Cross-service dependencies must be via explicit contracts (API, events, storage contracts), not implicit in-process coupling.
- Shared resources should expose stable outputs; service templates consume those outputs without transferring ownership.

## Microservice Boundaries (Diagram vs Ownership)

- The architecture diagram shows logical runtime boundaries (`MS1`, `MS2`, `MS3`, `MS4`), not CloudFormation/SAM ownership by itself.
- Template/resource ownership is defined as:
  - `b-infra`:
    - Shared/foundational platform resources only (CloudFront, hosting S3, Route53, ACM, shared buckets, baseline logging/observability, and explicitly shared wiring).
  - `b-ms1-ingress`:
    - Ingress service resources in its own SAM template (upload-init API/Lambda and service-specific IAM/config).
  - `b-ms2-detection`:
    - Detection service resources in its own SAM template (worker Lambda, Rekognition integration, service-specific IAM/config).
  - `b-ms3-faces`:
    - Face extraction service resources in its own SAM template (worker Lambda and service-specific IAM/config).
  - `b-ms4-statemgr`:
    - State manager resources in its own SAM template (state API/Lambda/table(s) unless explicitly marked shared).
- Rule of precedence when unclear:
  - Keep `b-infra` for shared foundation.
  - Keep business-service resources inside the owning microservice template.
  - If a resource seems shared, document ownership explicitly before implementation.

## Technology Baseline

- OS target for development: Fedora 43+.
- Frontend: React + TypeScript.
- Backend: Python 3.12 on AWS SAM.
- Python environment for automation/agent work: `conda_py_env_312`.

## Current Status

Project is in bootstrap/setup phase.
Code, tests, and execution scripts are being created incrementally, with documentation-first guidance to keep work stateless and easy to continue.

## Next Milestones

- Finalize per-module `README.md` files with canonical `install`/`test`/`lint`/`run` commands.
- Scaffold SAM backend services and shared infra.
- Scaffold frontend SPA and upload workflow.
- Define initial end-to-end flow contract between frontend and ingress microservice.
