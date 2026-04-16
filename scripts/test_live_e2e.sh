#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

SCRIPT_NAME="test_live_e2e"
SUMMARY_HEADER="Live E2E Smoke Summary"
source "${ROOT_DIR}/scripts/_test_lib.sh"
load_test_config

MS1_API_BASE_URL="${MS1_API_BASE_URL:-}"
MS4_API_BASE_URL="${MS4_API_BASE_URL:-}"
SMOKE_CLASS_PASSWORD="${SMOKE_CLASS_PASSWORD:-}"

if [ -z "${MS1_API_BASE_URL}" ] || [ -z "${MS4_API_BASE_URL}" ]; then
  echo "MS1_API_BASE_URL and MS4_API_BASE_URL must be set (env or scripts/testing.env)."
  exit 2
fi

if [ -z "${SMOKE_CLASS_PASSWORD}" ]; then
  echo "SMOKE_CLASS_PASSWORD must be set for live e2e smoke (env or scripts/testing.env.local)."
  exit 2
fi

SMOKE_NICKNAME="${SMOKE_NICKNAME:-smokeuser}"
SMOKE_SESSION_ID="${SMOKE_SESSION_ID:-smoke-session-$(date -u +%Y%m%d-%H%M%S)}"
SMOKE_FILE_PATH="${SMOKE_FILE_PATH:-img/ita-arch-diag1.png}"
SMOKE_CONTENT_TYPE="${SMOKE_CONTENT_TYPE:-image/png}"
POLL_COUNT="${SMOKE_POLL_COUNT:-8}"
POLL_INTERVAL_SECONDS="${SMOKE_POLL_INTERVAL_SECONDS:-3}"
EXPECTED_FINAL_STATUS="${SMOKE_EXPECTED_FINAL_STATUS:-queued}"

TMP_DIR="${ROOT_DIR}/tmp/test-reports"
mkdir -p "${TMP_DIR}"

INIT_BODY="${TMP_DIR}/live-e2e-init.json"
INIT_HEADERS="${TMP_DIR}/live-e2e-init.headers"
PUT_HEADERS="${TMP_DIR}/live-e2e-put.headers"
POLL_LOG="${TMP_DIR}/live-e2e-poll.log"

run_check \
  "ms1-init" \
  "MS1 init accepts valid class password" \
  bash -c "code=\$(curl -sS -D '${INIT_HEADERS}' -o '${INIT_BODY}' -w '%{http_code}' -H 'Content-Type: application/json' -X POST --data '{\"password\":\"${SMOKE_CLASS_PASSWORD}\",\"nickname\":\"${SMOKE_NICKNAME}\",\"sessionId\":\"${SMOKE_SESSION_ID}\",\"contentType\":\"${SMOKE_CONTENT_TYPE}\",\"originalFilename\":\"$(basename "${SMOKE_FILE_PATH}")\"}' '${MS1_API_BASE_URL%/}/v1/uploads/init'); [ \"\${code}\" = '200' ]"

run_check \
  "init-envelope" \
  "MS1 init response carries uploadUrl/uploadId/objectKey" \
  bash -c "jq -e '.accepted == true and (.uploadId|length > 0) and (.uploadUrl|length > 0) and (.objectKey|length > 0)' '${INIT_BODY}' >/dev/null"

run_check \
  "s3-upload" \
  "Presigned S3 PUT upload succeeds" \
  bash -c "UPLOAD_URL=\$(jq -r '.uploadUrl' '${INIT_BODY}'); [ -n \"\${UPLOAD_URL}\" ] && [ \"\${UPLOAD_URL}\" != 'null' ] && code=\$(curl -sS -D '${PUT_HEADERS}' -o /dev/null -w '%{http_code}' -X PUT -H 'Content-Type: ${SMOKE_CONTENT_TYPE}' --upload-file '${SMOKE_FILE_PATH}' \"\${UPLOAD_URL}\") && [ \"\${code}\" = '200' ]"

run_check \
  "ms4-poll" \
  "MS4 status poll reaches expected phase for current implementation" \
  bash -c "UPLOAD_ID=\$(jq -r '.uploadId' '${INIT_BODY}'); : > '${POLL_LOG}'; for i in \$(seq 1 ${POLL_COUNT}); do body=\$(curl -sS '${MS4_API_BASE_URL%/}/v1/uploads/'\"\${UPLOAD_ID}\"'/status'); echo \"\${body}\" >> '${POLL_LOG}'; status=\$(echo \"\${body}\" | jq -r '.status // empty'); if [ \"\${status}\" = '${EXPECTED_FINAL_STATUS}' ]; then exit 0; fi; sleep ${POLL_INTERVAL_SECONDS}; done; exit 1"

finalize_and_exit
