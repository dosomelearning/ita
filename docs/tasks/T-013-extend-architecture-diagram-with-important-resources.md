# T-013: Extend Architecture Diagram with Important Resources

## Metadata

- Status: `todo`
- Created: `2026-03-09`
- Last Updated: `2026-03-09`
- Related Backlog Item: `T-013`
- Related Modules: `img/ita-arch-diag1.png`, `README.md`, `ARCHITECTURE.md`, `b-infra/README.md`, `f-spa/README.md`

## Context

Current architecture docs and ADs reference important resources/flows that are not all clearly visible in the current diagram.

The preferred direction is to extend the existing `img/ita-arch-diag1.png` for completeness rather than introducing a separate parallel diagram.

## Scope

In scope:

- Extend the existing architecture diagram (`img/ita-arch-diag1.png`) to better reflect key resources and runtime flows.
- Include currently underrepresented/high-value elements, including explicit frontend hosting path (`CloudFront -> S3 SPA hosting`) and other critical shared resources/flows already defined in docs/ADs.
- Keep naming and ownership boundaries consistent with README + module docs + AD log.

Out of scope:

- Full visual redesign of the diagram style.
- Introducing contradictory architecture changes not already documented/approved.

## AD Dependencies

- `AD-009`: Diagram should represent single processing bucket with prefix-level segmentation.
- `AD-011`: Diagram should show shared password source in SSM Parameter Store for `MS1`.
- `AD-014`: Diagram should make `CloudFront -> S3` SPA hosting path explicit.
- `AD-016`: Diagram should include explicit `MS1 -> MS4` upload-init state registration edge.
- `AD-017`: Diagram should represent centralized queue/DLQ ownership in `b-infra`.
- `AD-021`: Diagram should consistently reflect shared edge/domain/TLS platform layer (CloudFront, Route53, ACM).

## Acceptance Criteria

- [x] `T-013` added to active backlog with correct `T-###` ID sequencing.
- [ ] Diagram update plan is defined from existing architecture docs/ADs.
- [ ] Existing diagram is extended (preferred) or a clearly justified alternate produced.
- [ ] Updated diagram remains consistent with README and `ARCHITECTURE.md` decisions.

## Implementation Notes

- Prefer incremental extension of current diagram to preserve continuity.
- Keep diagram readable; add only architecture-significant resources/flows.

### Diagram Alignment Checklist (from current ADs)

- Add explicit `MS1` shared-password source as **SSM Parameter Store** (`AD-011`).
- Clarify frontend hosting path as **CloudFront -> S3 SPA hosting bucket** (`AD-014`).
- Reflect **single processing bucket** architecture with prefix-level segmentation (for example `uploads/`, `rekognition/`, `faces/`) instead of implying three physically separate buckets (`AD-009`).
- Optionally annotate `MS3` extraction implementation as **Pillow-based** if diagram detail level allows (`AD-013`).
- Ensure diagram remains consistent with already-visible decisions:
  - Two API Gateway surfaces (`MS1` ingress and `MS4` state) (`AD-008`).
  - Explicit `MS1 -> MS4` upload-init state registration edge (`AD-016`).
  - SQS + DLQ async boundaries (`AD-003`, `AD-010`).
  - Rekognition used by `MS2` only (`AD-012`).

## Validation Evidence

- Command(s) run:
  - `sed -n '1,140p' docs/system-checklist.md`
  - `sed -n '1,220p' ARCHITECTURE.md`
- Manual checks:
  - Confirmed user preference to extend existing diagram for completeness.
- Output summary:
  - Backlog task opened for diagram extension work.

## Change Log

- `2026-03-09` - Initial task file created.
