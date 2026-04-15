#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

SCRIPT_NAME="test_live_basic"
SUMMARY_HEADER="Live Basic Test Summary"
source "${ROOT_DIR}/scripts/_test_lib.sh"
load_test_config

MS1_API_BASE_URL="${MS1_API_BASE_URL:-}"
MS4_API_BASE_URL="${MS4_API_BASE_URL:-}"

if [ -z "${MS1_API_BASE_URL}" ] || [ -z "${MS4_API_BASE_URL}" ]; then
  echo "MS1_API_BASE_URL and MS4_API_BASE_URL must be set (env or scripts/testing.env)."
  exit 2
fi

TMP_DIR="${ROOT_DIR}/tmp/test-reports"
mkdir -p "${TMP_DIR}"

MISSING_UPLOAD_ID="integration-missing-id"
MS4_MISSING_BODY="${TMP_DIR}/ms4-missing-upload.json"
MS1_INVALID_BODY="${TMP_DIR}/ms1-invalid-password.json"
MS1_INVALID_PASSWORD="${MS1_INVALID_PASSWORD:-wrong-password}"

run_check \
  "ms4-missing" \
  "MS4 missing upload returns HTTP 404" \
  bash -c "[ \"\$(curl -sS -o '${MS4_MISSING_BODY}' -w '%{http_code}' '${MS4_API_BASE_URL%/}/v1/uploads/${MISSING_UPLOAD_ID}/status')\" = '404' ]"

run_check \
  "ms4-envelope" \
  "MS4 missing upload error code validation" \
  bash -c "jq -e '.error.code == \"UPLOAD_NOT_FOUND\" and (.requestId|length > 0) and (.timestamp|length > 0)' '${MS4_MISSING_BODY}' >/dev/null"

run_check \
  "ms1-invalid" \
  "MS1 invalid password returns HTTP 401/403" \
  bash -c "code=\$(curl -sS -o '${MS1_INVALID_BODY}' -w '%{http_code}' -H 'Content-Type: application/json' -X POST --data '{\"password\":\"${MS1_INVALID_PASSWORD}\",\"nickname\":\"smoke-user\",\"sessionId\":\"smoke-session-live-basic\",\"contentType\":\"image/jpeg\"}' '${MS1_API_BASE_URL%/}/v1/uploads/init'); [ \"\${code}\" = '401' ] || [ \"\${code}\" = '403' ]"

run_check \
  "ms1-envelope" \
  "MS1 invalid password error code validation" \
  bash -c "jq -e '.error.code == \"INVALID_PASSWORD\" and (.requestId|length > 0) and (.timestamp|length > 0)' '${MS1_INVALID_BODY}' >/dev/null"

run_check \
  "ms4-itest" \
  "MS4 integration test script" \
  bash -c "MS4_API_BASE_URL='${MS4_API_BASE_URL%/}' ./b-ms4-statemgr/scripts/run_integration_tests.sh"

finalize_and_exit
