# T-003: Set Up b-infra Shared Stack

## Metadata

- Status: `todo`
- Created: `2026-03-08`
- Last Updated: `2026-03-08`
- Related Backlog Item: `T-003`
- Related Modules: `b-infra`, `docs/system-checklist.md`

## Context

The project needs a shared infrastructure baseline before service-specific stacks are created.
`b-infra` is the first stack in deployment order and owns shared/foundational resources only.

## Scope

In scope:

- Define `b-infra` CloudFormation template as canonical source of truth for shared resources.
- Establish `b-infra` as first stack to create for this project.
- Include shared resource categories in `b-infra`:
  - CloudFront
  - Route53
  - ACM
  - S3 bucket for frontend hosting
  - SQS queues and DLQs
  - SNS topics/subscriptions (to be determined)
  - Single shared S3 bucket for uploaded photos and processing artifacts
  - Initial artifact prefix plan in that bucket:
    - `uploaded/`
    - `processed/`
    - `rekognition/`
    - `faces/`
  - Shared observability/logging resources as needed for platform baseline

Out of scope:

- Full resource-by-resource listing in this task spec.
- Service-owned resources for `b-ms1`..`b-ms4`.
- Deployment execution.

## Acceptance Criteria

- [ ] `b-infra` documentation states it is the first stack in creation order.
- [ ] `b-infra` template ownership is documented as source of truth for shared resources.
- [ ] Shared resource categories listed in this task are represented in `b-infra` docs/template planning.
- [ ] Queue ownership model is explicitly documented:
  - Cross-service boundary queues and their DLQs are owned by `b-infra`.
  - Microservice stacks own queue-consumer wiring only (event mappings, service IAM, consumer runtime tuning).
- [ ] Queue contract documentation plan exists (payload schema, versioning, retry semantics, DLQ replay procedure).
- [ ] SNS decision rule is documented (system-level messaging/alarms only at current stage).
- [ ] Shared artifact storage decision is documented (single bucket + prefix layout).
- [ ] S3 event notification routing for uploaded photos to boundary SQS queue is documented in `b-infra` planning/template notes.

## Implementation Notes

- Keep shared vs service-owned boundary explicit.
- Avoid moving microservice-owned resources into `b-infra`.
- Detailed resource definitions remain in template and module docs.
- Baseline shared resource categories are documented in this task and should drive `b-infra` template planning directly.
- Ownership findings for queue infrastructure:
  - `b-infra` owns cross-service SQS queues and DLQs that define inter-service boundaries.
  - Service stacks (`b-ms2`, `b-ms3`, and others when applicable) own only consumption integration:
    - Lambda event source mapping
    - Consumer IAM permissions
    - Handler-specific batch/retry tuning
- Contract responsibilities:
  - Queue resource ownership and message-contract ownership are separate concerns.
  - Resource lifecycle belongs to `b-infra`; contract/schema lifecycle must be documented as shared inter-service contract.
- Shared S3 artifact storage decision:
  - Use one shared processing bucket for uploaded photos and generated artifacts.
  - Separate content by prefixes:
    - `uploaded/`
    - `processed/`
    - `rekognition/`
    - `faces/`
  - Additional prefixes may be introduced later as pipeline needs evolve.
- Eventing decision:
  - Configure S3 event notifications from the shared processing bucket to the appropriate boundary SQS queue for new uploaded photos.
  - Trigger notifications only for object-created events under the `uploaded/` prefix.
  - Do not configure S3->SQS notifications for `processed/`, `rekognition/`, or `faces/`; those prefixes are microservice-internal processing outputs.
  - Since both S3 bucket and queues are owned in `b-infra`, keep notification wiring managed in the same stack.
- SNS usage decision:
  - Current planned SNS usage is system-level messaging (for example, solution-wide alarms/notifications).
  - No SNS-based inter-service event fan-out is planned at this stage.
  - For linear stage-to-stage pipeline transitions, use direct SQS handoff.

## Validation Evidence

- Command(s) run:
  - `sed -n '1,220p' docs/system-checklist.md`
- Manual checks:
  - Confirmed `T-003` backlog item exists and links this task file.
- Output summary:
  - Backlog and detailed planning entry created.

## Change Log

- `2026-03-08` - Initial draft.
