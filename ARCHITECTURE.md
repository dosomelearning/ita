# Architecture Decisions and Rationale

This document captures architectural decisions, their rationale, and key tradeoffs for `4-ita`.
It complements the root [`README.md`](README.md), which remains the architecture entry point and system overview.

## Architecture Diagram

![4-ita architecture](img/ita-arch-diag1.png)

Source image: `img/ita-arch-diag1.png`.
The diagram is intentionally simplified; canonical ownership, contract boundaries, and implementation semantics are defined by the AD entries below.

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
- [AD-012: Keep Rekognition usage in `MS2` for face detection and location metadata](#ad-012-keep-rekognition-usage-in-ms2-for-face-detection-and-location-metadata)
- [AD-013: Use Pillow in `MS3` for face extraction from Rekognition coordinates](#ad-013-use-pillow-in-ms3-for-face-extraction-from-rekognition-coordinates)
- [AD-014: Host the SPA from S3 behind CloudFront](#ad-014-host-the-spa-from-s3-behind-cloudfront)
- [AD-015: Use CloudWatch Logs as baseline logging across all microservices](#ad-015-use-cloudwatch-logs-as-baseline-logging-across-all-microservices)
- [AD-016: Record upload-init state in `MS4` via synchronous `MS1 -> MS4` call](#ad-016-record-upload-init-state-in-ms4-via-synchronous-ms1---ms4-call)
- [AD-017: Keep processing queues and DLQs centralized in `b-infra`](#ad-017-keep-processing-queues-and-dlqs-centralized-in-b-infra)
- [AD-018: Manage infrastructure through IaC-only workflow](#ad-018-manage-infrastructure-through-iac-only-workflow)
- [AD-019: Use serverless cloud-native managed AWS architecture as default style](#ad-019-use-serverless-cloud-native-managed-aws-architecture-as-default-style)
- [AD-020: Use centralized baseline alarms with metric-specific rationale](#ad-020-use-centralized-baseline-alarms-with-metric-specific-rationale)
- [AD-021: Use shared edge/domain/TLS platform services in `b-infra`](#ad-021-use-shared-edgedomaintls-platform-services-in-b-infra)

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
- Queue/DLQ ownership for this workflow is centralized in shared infrastructure as defined in `AD-017`.

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

### AD-012: Keep Rekognition usage in `MS2` for face detection and location metadata

- Status: `accepted`
- Date: `2026-03-09`

Context:

- `MS2` is the detection microservice and the only stage that performs face detection.
- `MS3` consumes detection output to extract and store face crops; it does not own detection.
- Rekognition returns structured detection JSON that includes face presence and location data needed downstream.

Decision:

- Keep Amazon Rekognition integration owned by `MS2` only.
- Use `MS2` to detect whether faces exist in uploaded photos.
- Persist/publish detection metadata (including face location coordinates) for downstream extraction by `MS3`.
- `MS3` consumes extraction jobs from faces SQS and processes the original photo using Rekognition artifacts persisted in S3.

Why:

- Keeps detection responsibility in one service boundary.
- Avoids duplicate detection logic or API usage across multiple services.
- Provides a clear contract: `MS2` produces detection metadata, `MS3` performs extraction based on that metadata.
- Enables short-circuiting: photos with zero detected faces do not enter extraction processing.
- Preserves Lambda specialization so detection and extraction complexity do not accumulate in one function.
- Keeps extraction asynchronously decoupled from `MS2` through queue + artifact contracts.

Alternatives considered:

- Run Rekognition directly in `MS3` during extraction.
  - Rejected: mixes service responsibilities and duplicates detection concerns.
- Invoke Rekognition from multiple services.
  - Rejected: increases coupling, cost/control complexity, and contract ambiguity.

Consequences:

- Positive:
  - Clear ownership of detection logic and IAM permissions.
  - Stable downstream contract based on detection JSON (including bounding locations).
  - Lower unnecessary extraction workload/cost for no-face inputs.
  - Simpler and more maintainable Lambda responsibilities per service.
  - `MS3` can continue processing from SQS/S3 contracts without direct runtime coupling to `MS2`.
- Tradeoff:
  - `MS3` depends on quality/completeness of `MS2` detection artifacts and schema discipline.

### AD-013: Use Pillow in `MS3` for face extraction from Rekognition coordinates

- Status: `accepted`
- Date: `2026-03-09`

Context:

- `MS2` provides face location metadata from Rekognition.
- `MS3` must crop/extract face images from original photos using those coordinates.

Decision:

- Use `Pillow` as the primary image-processing library in `MS3` for coordinate-based face extraction.
- Keep Rekognition usage limited to detection/metadata in `MS2`; do not use Rekognition for extraction.

Why:

- Fits the current requirement: deterministic crop/resize based on already available coordinates.
- Keeps dependency footprint lighter and implementation simpler for current project scale.
- Aligns with service specialization: detection in `MS2`, extraction in `MS3`.

Alternatives considered:

- `opencv-python-headless` as primary extractor.
  - Deferred: useful for advanced transforms, but higher complexity/footprint than needed now.
- Additional face-analysis libraries.
  - Rejected for this flow: unnecessary because detection/localization is already provided by Rekognition in `MS2`.

Consequences:

- Positive:
  - Simple and maintainable extraction implementation path in `MS3`.
  - Lower runtime/package complexity for current needs.
- Tradeoff:
  - If future quality requirements demand advanced image operations, dependency set may need to expand.

### AD-014: Host the SPA from S3 behind CloudFront

- Status: `accepted`
- Date: `2026-03-09`

Context:

- The frontend is a static SPA (`f-spa`) and does not require server-side rendering in current scope.
- Existing infra docs already define CloudFront + frontend hosting S3 in `b-infra`.

Decision:

- Host SPA build artifacts in S3 and deliver them through CloudFront.
- Keep frontend hosting resources as shared foundational infrastructure under `b-infra`.

Why:

- Matches static SPA delivery model with low operational overhead.
- Provides a clear separation between frontend asset delivery and backend API services.
- Aligns with existing project ownership model for shared platform resources.

Alternatives considered:

- Host SPA via compute service (for example server-side frontend runtime).
  - Rejected for current phase: unnecessary complexity for static SPA requirements.

Consequences:

- Positive:
  - Simpler deployment/operations path for frontend delivery.
  - Clear infra ownership and consistent edge delivery entrypoint.
- Tradeoff:
  - Runtime backend endpoint configuration must be managed explicitly in frontend environment config.
- Diagram note:
  - Current architecture diagram does not clearly show all important shared resources (including explicit frontend S3 hosting path).
  - Tracked for diagram extension in `T-013`.

### AD-015: Use CloudWatch Logs as baseline logging across all microservices

- Status: `accepted`
- Date: `2026-03-09`

Context:

- All backend microservices are Lambda-based and require operational visibility for troubleshooting and flow tracing.
- Observability must be consistent across ingress, detection, extraction, and state services.

Decision:

- Use Amazon CloudWatch Logs as the baseline centralized logging sink for all microservice Lambdas.
- Emit structured logs for key lifecycle and error events in each service.

Why:

- Native Lambda integration with low setup overhead.
- Single operational location for debugging, issue triage, and flow-level tracing.
- Consistent logging baseline supports staged growth of observability practices.

Alternatives considered:

- Mixed/custom per-service logging destinations from the start.
  - Rejected for current phase: unnecessary complexity and fragmented operations for current scale.

Consequences:

- Positive:
  - Unified log discovery/triage workflow across services.
  - Simpler baseline operations while services are still being scaffolded.
- Tradeoff:
  - Log schema discipline is required to keep logs queryable across services.
  - Retention/cost tuning must be managed explicitly as volume grows.
- Guardrails:
  - Do not log secrets or sensitive personal data.
  - Keep correlation identifiers in logs to trace multi-service flows.

### AD-016: Record upload-init state in `MS4` via synchronous `MS1 -> MS4` call

- Status: `accepted`
- Date: `2026-03-09`

Context:

- `MS4` is the authoritative workflow state manager.
- Upload-init is the first accepted workflow event and should be reflected in state timeline.
- Current docs had `MS1 -> MS4` registration as optional.

Decision:

- `MS1` must record upload-init state in `MS4` for accepted admission/init requests.
- Integration mode for current phase is synchronous `MS1 -> MS4` API call.
- If state registration fails, init flow should fail with retriable error rather than proceeding with divergent state.

Why:

- Keeps `MS4` as single source of workflow truth from the first accepted step.
- Avoids state gaps where later stages exist without authoritative initialization record.
- Keeps current-phase implementation simpler than introducing additional async init channel.

Alternatives considered:

- Keep init registration optional.
  - Rejected: weak state authority and inconsistent workflow timeline.
- Use async-only init event from `MS1` to `MS4`.
  - Deferred: can reduce runtime coupling later, but adds delivery/retry complexity now.

Consequences:

- Positive:
  - Stronger state consistency at workflow entry.
  - Clear ownership split: `MS1` admission, `MS4` authoritative state.
- Tradeoff:
  - Introduces runtime dependency of `MS1` on `MS4` availability for accepted requests.
- Future direction:
  - Reevaluate async/outbox approach if coupling or reliability pressure increases.
  - Refine this AD with explicit state-transition details after `T-010` finalizes frontend/backend interaction and state-read contracts.

Implementation note:

- Detailed state/read interaction mapping is tracked as a separate task in `T-010` (`docs/tasks/T-010-define-frontend-backend-exchange-contracts.md`).

### AD-017: Keep processing queues and DLQs centralized in `b-infra`

- Status: `accepted`
- Date: `2026-03-09`

Context:

- The workflow uses cross-service queues (`uploaded photos`, `faces extraction`) and paired DLQs.
- Queue contracts are part of shared event backbone behavior across microservices.
- Team preference is to keep these resources independent from individual microservice stacks.

Decision:

- Keep processing queues and their DLQs in shared infrastructure (`b-infra`) rather than service-owned templates.
- Expose queue identifiers/ARNs as stable infra outputs for consuming service stacks.

Why:

- Separates shared event backbone lifecycle from individual microservice deployment lifecycle.
- Reduces risk of queue resource churn/replacement during service-level changes.
- Centralizes queue governance (naming, encryption, retention defaults, and alarms) in one place.

Alternatives considered:

- Service-owned queue+DLQ per consuming microservice.
  - Rejected for current direction: stronger service autonomy, but more distributed queue governance and higher coordination burden for shared contract changes.

Consequences:

- Positive:
  - Independent queue lifecycle and simpler shared operations/observability.
  - Clear infra-level management point for queue baseline controls.
- Tradeoff:
  - Queue evolution now requires explicit cross-stack coordination with dependent services.
  - Over-centralization risk if contract ownership is not clearly documented.
- Guardrails:
  - Treat each queue as an explicit cross-service contract with documented producer/consumer responsibilities.
  - Keep least-privilege IAM boundaries per queue for producer and consumer roles.
  - Require contract-impact review before queue attribute/schema/routing changes.

### AD-018: Manage infrastructure through IaC-only workflow

- Status: `accepted`
- Date: `2026-03-09`

Context:

- The project uses CloudFormation/SAM stacks across shared infrastructure and microservices.
- Manual console-driven changes increase drift risk and reduce reproducibility.

Decision:

- Treat Infrastructure as Code as the required/default path for infrastructure changes.
- Do not rely on manual console edits as a standard operations workflow.
- If emergency break-glass changes are applied manually, they must be documented and back-ported to IaC immediately after stabilization.

Why:

- Preserves reproducibility and environment parity.
- Improves auditability and change traceability across stacks.
- Reduces hidden configuration drift and recovery uncertainty.

Alternatives considered:

- Mixed IaC + ad-hoc manual infrastructure operations.
  - Rejected: higher drift probability and weaker lifecycle control.

Consequences:

- Positive:
  - More predictable deployments and safer infrastructure evolution.
  - Stronger alignment between declared and runtime state.
- Tradeoff:
  - Slower ad-hoc changes compared with direct console modifications.
- Guardrails:
  - Break-glass changes are exceptional and temporary.
  - Every manual emergency change must be captured in IaC and reviewed as soon as possible.

### AD-019: Use serverless cloud-native managed AWS architecture as default style

- Status: `accepted`
- Date: `2026-03-09`

Context:

- Project goals emphasize resilient operation for bursty classroom usage with low operational overhead.
- Current architecture already centers on managed AWS services and event-driven workflows.

Decision:

- Adopt serverless cloud-native architecture as the default system style.
- Prefer managed AWS services (for compute, integration, storage, edge delivery, and observability) over self-managed runtime infrastructure.

Why:

- Aligns with project intent: low-operations, resilient, event-driven architecture.
- Reduces infrastructure management burden and enables focus on service contracts and workflow behavior.
- Improves scaling/failure handling characteristics for periodic burst workloads.

Alternatives considered:

- Mixed or primarily self-managed runtime infrastructure.
  - Rejected for current phase: higher operational complexity and weaker fit with project goals.

Consequences:

- Positive:
  - Faster iteration on business workflow with less platform-management overhead.
  - Strong alignment with AWS-native integration patterns used in this system.
- Tradeoff:
  - Architecture remains coupled to managed AWS service model and constraints.
- Guardrails:
  - Depart from serverless/managed defaults only when a concrete requirement cannot be met adequately by current managed options, and document such exceptions explicitly.

### AD-020: Use centralized baseline alarms with metric-specific rationale

- Status: `accepted`
- Date: `2026-03-09`

Context:

- The system has public APIs and asynchronous queue-driven processing stages where failures can be silent without alerting.
- Logging baseline is already defined (`AD-015`), but alerting policy must define what constitutes operational risk.

Decision:

- Keep baseline alarm resources centralized in `b-infra`.
- Route baseline alarms to a shared SNS topic.
- Start with low-noise, failure-focused alarms and tune thresholds after initial real runs.

What we observe and why:

- API Gateway `5xx` and throttles:
  - Why: detect backend/API availability issues and capacity pressure at public entry points.
- API Gateway abnormal `4xx` spikes:
  - Why: detect admission misuse, client integration breakage, or rate-limit pressure trends.
- Lambda errors and throttles (all microservices):
  - Why: detect broken service behavior and compute-level capacity/concurrency pressure.
- SQS DLQ visible messages (`> 0`):
  - Why: detect failed processing requiring investigation/replay.
- SQS backlog and message age (sustained):
  - Why: detect processing lag before it becomes end-user-visible failure.

Severity model:

- `critical`: immediate operational action likely required (for example DLQ non-empty, sustained Lambda/API failures).
- `warning`: degradation/risk trend requiring monitoring or near-term adjustment (for example growing queue age/backlog or elevated `4xx` patterns).

Alternatives considered:

- Service-by-service independent alarm stacks only.
  - Rejected for current phase: fragmented operations and inconsistent baseline coverage.
- Dashboard-first approach before baseline alarms.
  - Deferred: dashboard can be added later; alarm coverage is prioritized first.

Consequences:

- Positive:
  - Unified and predictable incident-detection baseline across services.
  - Faster triage through centralized alerting entrypoint.
- Tradeoff:
  - Initial thresholds may need iterative tuning to balance missed signals vs alert noise.
- Implementation note:
  - CloudWatch dashboarding is considered valuable but intentionally deferred for the current phase.

### AD-021: Use shared edge/domain/TLS platform services in `b-infra`

- Status: `accepted`
- Date: `2026-03-09`

Context:

- Frontend/public access requires reliable edge delivery, DNS resolution, and TLS certificate management.
- Existing infra/module docs already place these concerns in shared foundational infrastructure.

Decision:

- Keep edge/domain/TLS platform services in `b-infra` as shared foundational components:
  - CloudFront for edge delivery entrypoint.
  - Route53 for DNS/domain routing.
  - ACM for certificate lifecycle and TLS enablement.

Why:

- These are cross-cutting platform capabilities used by multiple modules/environments.
- Centralized ownership avoids duplication and inconsistent domain/certificate handling.
- Supports clean separation between platform delivery concerns and microservice business logic.

Alternatives considered:

- Service-owned DNS/TLS/edge resources per microservice.
  - Rejected for current direction: duplicated configuration and weaker platform coherence.

Consequences:

- Positive:
  - Consistent public-entry configuration and shared platform governance.
  - Simpler consumer modules that rely on stable infra outputs.
- Tradeoff:
  - Edge/domain changes are coordinated through shared infra lifecycle.
- Scope note:
  - This AD is intentionally cumulative and can be refined later with service-level detail for additional shared platform resources.
