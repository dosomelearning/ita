# Architecture Decisions and Rationale

This document captures architectural decisions, their rationale, and key tradeoffs for `4-ita`.
It complements the root [`README.md`](README.md), which remains the architecture entry point and system overview.

## Architecture Diagram

![4-ita architecture](img/ita-arch-diag1.png)

Source image: `img/ita-arch-diag1.png`.

## Role of This File

- `README.md`:
  - System overview, boundaries, and high-level architecture map.
- `ARCHITECTURE.md`:
  - Decision rationale, alternatives considered, and explicit tradeoffs.

This split keeps onboarding simple while preserving deeper engineering reasoning in a stable location.

## Decision Index

- [AD-001: Keep architecture overview in `README.md` and detailed rationale in `ARCHITECTURE.md`](#ad-001-keep-architecture-overview-in-readmemd-and-detailed-rationale-in-architecturemd)
- [AD-002: Define shared-infra vs service-owned resource boundaries](#ad-002-define-shared-infra-vs-service-owned-resource-boundaries)
- [AD-003: Keep queue-based asynchronous boundaries between processing services](#ad-003-keep-queue-based-asynchronous-boundaries-between-processing-services)
- [AD-004: Enforce shared-password admission at `MS1` before protected flow](#ad-004-enforce-shared-password-admission-at-ms1-before-protected-flow)
- [AD-005: Enforce API Gateway rate limiting on all public endpoints](#ad-005-enforce-api-gateway-rate-limiting-on-all-public-endpoints)
- [AD-006: Enforce classroom-limited data lifecycle for EU-context runs](#ad-006-enforce-classroom-limited-data-lifecycle-for-eu-context-runs)
- [AD-007: Use a single `main` branch workflow for this phase](#ad-007-use-a-single-main-branch-workflow-for-this-phase)
- [AD-008: Keep two API Gateway APIs aligned to `MS1` and `MS4` service purposes](#ad-008-keep-two-api-gateway-apis-aligned-to-ms1-and-ms4-service-purposes)
- [AD-009: Use one processing bucket with prefix-level isolation and policy controls](#ad-009-use-one-processing-bucket-with-prefix-level-isolation-and-policy-controls)
- [AD-010: Use two Lambda execution modes (API sync and SQS async)](#ad-010-use-two-lambda-execution-modes-api-sync-and-sqs-async)
- [AD-011: Store shared class password in SSM Parameter Store and keep DynamoDB for `MS4` state](#ad-011-store-shared-class-password-in-ssm-parameter-store-and-keep-dynamodb-for-ms4-state)

## Decision Log

### AD-001: Keep architecture overview in `README.md` and detailed rationale in `ARCHITECTURE.md`

- Status: `accepted`
- Date: `2026-03-09`

Context:

- The project needs clearer explanation of architecture decisions.
- The root `README.md` is already defined as architecture source-of-truth entrypoint.
- Placing all deep rationale directly in `README.md` would reduce readability for new readers.

Decision:

- Keep high-level architecture narrative in root `README.md`.
- Store detailed architecture decision rationale in root `ARCHITECTURE.md`.
- Link both ways:
  - `README.md` links to `ARCHITECTURE.md`.
  - `ARCHITECTURE.md` references `README.md` and module docs.

Alternatives considered:

- Put all rationale into `README.md` only.
  - Rejected: too heavy for onboarding and quick project scanning.
- Put detailed architecture in `docs/ARCHITECTURE.md`.
  - Rejected: this project keeps `docs/` focused on operational process/tracking; architecture intent is top-level project context.

Consequences:

- Positive:
  - Better onboarding readability.
  - Stable location for explicit decisions and tradeoffs.
  - Easier consistency checks across module READMEs.
- Cost:
  - Two linked docs must stay synchronized.

### AD-002: Define shared-infra vs service-owned resource boundaries

- Status: `accepted`
- Date: `2026-03-09`

Context:

- The monorepo includes `b-infra` and four service modules, each with independent SAM ownership.
- Ambiguity in ownership can create coupling, deployment friction, and unclear responsibility.

Decision:

- Keep `b-infra` limited to shared foundational resources.
- Keep business-service resources in service-owned templates (`b-ms1-ingress`, `b-ms2-detection`, `b-ms3-faces`, `b-ms4-statemgr`).
- Resolve ambiguous ownership explicitly in documentation before implementation.

Why:

- Preserves microservice autonomy in a monorepo layout.
- Reduces accidental cross-service coupling and deployment coordination overhead.
- Keeps responsibilities auditable and easier to evolve independently.

Alternatives considered:

- Place most resources in `b-infra`.
  - Rejected: centralization would blur ownership and weaken service boundaries.

Consequences:

- Positive:
  - Clear ownership and safer independent iteration.
- Tradeoff:
  - Requires explicit cross-stack outputs/inputs and interface discipline.

### AD-003: Keep queue-based asynchronous boundaries between processing services

- Status: `accepted`
- Date: `2026-03-09`

Context:

- The system targets bursty classroom uploads and resilient processing across detection/extraction stages.
- The architecture diagram and current module docs already assume SQS-based decoupling.

Decision:

- Keep SQS-based async handoff boundaries between processing stages (`MS2` and `MS3`), with DLQ-based failure handling.
- DLQ ownership follows the same resource-boundary rule:
  - Service-owned by default with the owning microservice queue.
  - Treated as shared only when explicitly documented as a cross-service/shared resource in architecture docs.

Why:

- Improves resilience under bursty classroom uploads.
- Enables retry/isolation behavior across stages instead of hard synchronous failure chains.
- Supports independent scaling and operational triage.

Alternatives considered:

- Direct synchronous service-to-service orchestration.
  - Rejected: tighter runtime coupling and less robust behavior during partial failures/spikes.

Consequences:

- Positive:
  - Better fault isolation and scalability characteristics.
- Tradeoff:
  - Eventual consistency and more operational components (queues, retries, DLQs).

### AD-004: Enforce shared-password admission at `MS1` before protected flow

- Status: `accepted`
- Date: `2026-03-09`

Context:

- This project intentionally excludes Cognito.
- Upload initiation must be gated by instructor-managed shared password validation.

Decision:

- Validate shared class password in `MS1` before issuing presigned upload URL.
- Reject invalid requests before they can enter upload/processing workflow.

Why:

- Matches project constraint of no Cognito while still enforcing admission control.
- Limits unnecessary backend load and storage/event churn from unauthorized requests.
- Keeps access checks at a single explicit ingress boundary.

Alternatives considered:

- No password gate at ingress.
  - Rejected: inconsistent with access model and public-flow constraints.
- Add full identity provider now.
  - Rejected for current phase: out of scope for classroom demo and current project direction.

Consequences:

- Positive:
  - Clear and auditable admission model for current scope.
- Tradeoff:
  - Shared-secret model is simpler but less granular than per-user identity.

### AD-005: Enforce API Gateway rate limiting on all public endpoints

- Status: `accepted`
- Date: `2026-03-09`

Context:

- The project requires controlled public access and resilience under concurrent classroom usage.
- Current project constraints already state rate limiting as mandatory.

Decision:

- Require API Gateway throttling/rate limits for all frontend-exposed endpoints.

Why:

- Protects ingress/state APIs from burst spikes and accidental abuse.
- Stabilizes classroom behavior by controlling request pressure at public entry points.
- Aligns with project non-functional and security guardrails.

Alternatives considered:

- Application-only throttling without API Gateway limits.
  - Rejected: late enforcement point and weaker shared control plane behavior.

Consequences:

- Positive:
  - Predictable API behavior under concurrent load.
- Tradeoff:
  - Limits must be tuned to avoid false throttling during peak class usage.

### AD-006: Enforce classroom-limited data lifecycle for EU-context runs

- Status: `accepted`
- Date: `2026-03-09`

Context:

- The project is academic/demo-oriented and explicitly constrains data handling and retention.
- Data protection constraints are treated as core design requirements.

Decision:

- Treat classroom-time-boxed data handling and deletion as mandatory architecture constraints.
- Prohibit secondary reuse/retention of uploaded and derived face artifacts beyond class purpose/window.

Why:

- Aligns the system with declared academic-use and EU-context data handling requirements.
- Makes privacy constraints explicit at architecture level, not optional operational policy.

Alternatives considered:

- Keep retention/deletion as optional runbook guidance only.
  - Rejected: too weak for stated project constraints.

Consequences:

- Positive:
  - Clear boundary for implementation choices and operations.
- Tradeoff:
  - Additional deletion/retention enforcement work is required in service design and operations.

### AD-007: Use a single `main` branch workflow for this phase

- Status: `accepted`
- Date: `2026-03-09`

Context:

- This project is currently maintained by one developer.
- Current delivery process does not use CI/CD pipelines, PR reviews, or branch-based release workflows.

Decision:

- Use a single-branch (`main`) workflow in the current project phase.

Why:

- Keeps delivery flow simple and low-overhead for solo development.
- Matches current team size and tooling maturity.
- Reduces process overhead while architecture and core modules are still being established.

Alternatives considered:

- Feature-branch + PR workflow from the start.
  - Deferred: valuable for collaboration and governance, but not necessary for current solo setup.

Consequences:

- Positive:
  - Faster iteration with minimal process friction.
  - Simpler repository operations for current scope.
- Tradeoff:
  - Fewer guardrails than PR/CI-based workflows.
- Future direction:
  - Reassess and evolve to branch/PR/CI practices when team size, risk, or delivery needs increase.

### AD-008: Keep two API Gateway APIs aligned to `MS1` and `MS4` service purposes

- Status: `accepted`
- Date: `2026-03-09`

Context:

- The frontend has two distinct backend interaction purposes:
  - Upload admission/init (`MS1`).
  - Workflow state/result read (`MS4`).
- `MS1` and `MS4` are separate microservices with different responsibilities and evolution paths.

Decision:

- Keep two API Gateway APIs, one owned by `MS1` and one owned by `MS4`.

Why:

- Preserves service boundary clarity between write-like admission/init flows and read/state flows.
- Enables independent evolution, deployment, and throttling policies per API surface.
- Keeps API ownership consistent with service-owned SAM templates.

Alternatives considered:

- Single shared API Gateway for all frontend endpoints.
  - Deferred: possible later, but currently increases coupling and blurs service ownership.

Consequences:

- Positive:
  - Clear contract ownership and separation of concerns.
  - Better control of per-service rate limits and lifecycle changes.
- Tradeoff:
  - Two API base endpoints must be managed in frontend runtime configuration.

### AD-009: Use one processing bucket with prefix-level isolation and policy controls

- Status: `accepted`
- Date: `2026-03-09`

Context:

- The project stores multiple processing artifacts: uploaded photos, Rekognition outputs, and extracted faces.
- Current project phase prioritizes clarity and low operational overhead.

Decision:

- Use a single shared processing S3 bucket for app-processing data.
- Partition data by strict prefixes (for example `uploads/`, `rekognition/`, `faces/`).
- Enforce access boundaries with IAM and bucket policies at prefix scope.

Why:

- Simplifies infrastructure management for project scale.
- Reduces setup and cross-stack wiring overhead while preserving service separation via keyspace/policy boundaries.
- Keeps architecture easier to operate and explain in a classroom/demo context.

Alternatives considered:

- Separate S3 bucket per data domain or per service.
  - Deferred: stronger physical isolation, but more infrastructure and integration complexity for current scope.

Consequences:

- Positive:
  - Simpler infrastructure surface and deployment coordination.
  - Centralized baseline controls (encryption, block-public-access, logging, lifecycle policies).
- Tradeoff:
  - Lower physical isolation than multi-bucket design and larger bucket blast radius.
  - Policy and naming discipline become mandatory to avoid cross-domain access mistakes.
- Guardrails:
  - Bucket-level public access blocked.
  - Least-privilege policies restricted by prefix.
  - Prefix-filtered event wiring so only intended objects trigger downstream flows.

### AD-010: Use two Lambda execution modes (API sync and SQS async)

- Status: `accepted`
- Date: `2026-03-09`

Context:

- The system exposes frontend APIs and also runs queue-driven background processing stages.
- Current service responsibilities separate admission/state API flows (`MS1`, `MS4`) from processing workers (`MS2`, `MS3`).

Decision:

- Use two Lambda execution modes:
  - API mode: API Gateway invokes Lambda and returns synchronous HTTP responses.
  - Worker mode: Lambda event source mappings poll SQS and invoke Lambda asynchronously.
- For worker mode outputs:
  - Emit synchronous state-update calls to `MS4` where required.
  - Emit asynchronous downstream queue messages for next-stage processing (for example faces extraction queue).

Why:

- Aligns invocation style with interaction type:
  - Request/response for frontend-facing operations.
  - Event-driven processing for decoupled backend stages.
- Keeps async pipeline scalable and resilient while preserving explicit state projection in `MS4`.

Alternatives considered:

- Only synchronous API-driven orchestration.
  - Rejected: tighter coupling and weaker resilience under burst/failure conditions.
- Fully async pipeline including `MS4` updates.
  - Deferred: possible later, but current design keeps `MS4` update path explicit and simple.

Consequences:

- Positive:
  - Clear operational model for each Lambda type.
  - Better scaling/fault-isolation properties for heavy processing stages.
- Tradeoff:
  - Mixed integration modes require careful retry/idempotency/error-handling design for worker -> `MS4` update calls.

### AD-011: Store shared class password in SSM Parameter Store and keep DynamoDB for `MS4` state

- Status: `accepted`
- Date: `2026-03-09`

Context:

- Access to upload initialization is gated by a single shared class password in `MS1`.
- `MS4` owns workflow state and aggregation concerns that use DynamoDB.
- Mixing password/config storage with workflow state data would blur service boundaries.

Decision:

- Store the shared class password in SSM Parameter Store for `MS1` admission checks.
- Keep DynamoDB usage focused on `MS4` workflow state/aggregation.
- Do not use a shared password DynamoDB table in the current architecture.

Why:

- Parameter Store fits single-secret/configuration retrieval for current project scope.
- Keeps `MS1` password concern separate from `MS4` state model.
- Reduces cross-service coupling and avoids repurposing `MS4` data storage for unrelated concerns.

Alternatives considered:

- Store password in DynamoDB.
  - Rejected for current phase: unnecessary data-model overhead for a single secret and higher risk of boundary mixing.

Consequences:

- Positive:
  - Cleaner microservice boundaries and clearer data ownership.
  - Simpler mental model: `MS1` admission secret in Parameter Store, `MS4` state in DynamoDB.
- Tradeoff:
  - Requires explicit parameter naming, access policy, and rotation handling conventions.
