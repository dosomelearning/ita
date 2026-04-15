# Latest Manual Test Snapshot

- Generated: `2026-04-15T06:20:54Z`
- Source report directory: `tmp/test-reports`

## Overview

| Runner | Status | Generated At | Pass | Fail | Total |
|---|---|---|---:|---:|---:|
| test_local | pass | 2026-04-15T06:17:07Z | 4 | 0 | 4 |
| test_live_basic | pass | 2026-04-15T06:13:21Z | 5 | 0 | 5 |
| test_live_e2e | pass | 2026-04-15T06:13:22Z | 4 | 0 | 4 |

## test_local

- Generated At: `2026-04-15T06:17:07Z`

| Check ID | Result | Description | Message |
|---|---|---|---|
| ms1-unit | pass | MS1 unit tests | OK |
| ms4-unit | pass | MS4 unit tests | OK |
| spa-unit | pass | SPA unit tests | OK |
| spa-build | pass | SPA build | OK |

## test_live_basic

- Generated At: `2026-04-15T06:13:21Z`

| Check ID | Result | Description | Message |
|---|---|---|---|
| ms4-missing | pass | MS4 missing upload returns HTTP 404 | OK |
| ms4-envelope | pass | MS4 missing upload error code validation | OK |
| ms1-invalid | pass | MS1 invalid password returns HTTP 401/403 | OK |
| ms1-envelope | pass | MS1 invalid password error code validation | OK |
| ms4-itest | pass | MS4 integration test script | OK |

## test_live_e2e

- Generated At: `2026-04-15T06:13:22Z`

| Check ID | Result | Description | Message |
|---|---|---|---|
| ms1-init | pass | MS1 init accepts valid class password | OK |
| init-envelope | pass | MS1 init response carries uploadUrl/uploadId/objectKey | OK |
| s3-upload | pass | Presigned S3 PUT upload succeeds | OK |
| ms4-poll | pass | MS4 status poll reaches expected phase for current implementation | OK |

## Notes

- This file is generated from JSON artifacts under `tmp/test-reports`.
- Regenerate using: `./scripts/render_test_snapshot.sh`.
