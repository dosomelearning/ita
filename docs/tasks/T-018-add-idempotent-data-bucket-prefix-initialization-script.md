# T-018: Add Idempotent Data-Bucket Prefix Initialization Script

## Metadata

- Status: `done`
- Created: `2026-03-09`
- Last Updated: `2026-03-09`
- Related Backlog Item: `T-018`
- Related Modules: `b-infra/scripts/init_data_prefixes.sh`, `b-infra/README.md`, `docs/system-checklist.md`

## Context

The shared processing data bucket uses key-prefix conventions (`uploaded/`, `processed/`, `rekognition/`, `faces/`) as logical folder contracts.

An idempotent utility script improves repeatability and operational clarity by creating prefix marker objects safely.

## Scope

In scope:

- Add script under `b-infra/scripts/` that creates required data-bucket prefix markers.
- Keep script idempotent and safe to rerun.
- Resolve target bucket from stack outputs and use profile `dev` by default.
- Document usage in `b-infra/README.md`.

Out of scope:

- Changing bucket architecture or event wiring.
- Running script automatically from deploy flow.

## Acceptance Criteria

- [x] Script exists and is executable.
- [x] Script initializes required data prefixes idempotently.
- [x] Script emits clear user-facing progress output.
- [x] README includes script usage notes.
- [x] User validated script behavior and requested closure.

## Implementation Notes

- Prefix creation in S3 is implemented by zero-byte object uploads for `<prefix>/`.
- Script should be rerunnable without destructive behavior.

## Validation Evidence

- Command(s) run:
  - `bash -n b-infra/scripts/init_data_prefixes.sh`
- Manual checks:
  - Verified script follows stack-output lookup pattern and safe prefix marker creation flow.
- Output summary:
  - Added idempotent prefix initialization utility.

## Change Log

- `2026-03-09` - Initial task file created.
- `2026-03-09` - Marked done after successful user validation and explicit close instruction.
