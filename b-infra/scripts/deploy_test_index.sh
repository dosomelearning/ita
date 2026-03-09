#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

STACK_NAME="${STACK_NAME:-ita-infra}"
AWS_PROFILE="${AWS_PROFILE:-dev}"
AWS_REGION="${AWS_REGION:-eu-central-1}"

export AWS_CLI_AUTO_PROMPT=off
export AWS_PAGER=""
export AWS_EC2_METADATA_DISABLED=true

log() {
  printf '[deploy_test_index] %s\n' "$*"
}

abort() {
  printf '[deploy_test_index][error] %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || abort "Missing required command: $1"
}

require_cmd aws
require_cmd jq
require_cmd curl

WORK_FILE="$(mktemp /tmp/ita-index-XXXXXX.html)"
BODY_FILE="$(mktemp /tmp/ita-index-body-XXXXXX.txt)"
cleanup() {
  rm -f "${WORK_FILE}" "${BODY_FILE}"
}
trap cleanup EXIT

log "Starting test index deployment flow."
log "Stack: ${STACK_NAME}"
log "AWS profile: ${AWS_PROFILE}"
log "AWS region: ${AWS_REGION}"

STACK_JSON="$(aws cloudformation describe-stacks \
  --profile "${AWS_PROFILE}" \
  --region "${AWS_REGION}" \
  --stack-name "${STACK_NAME}" \
  --output json \
  --no-cli-pager)"

WEB_BUCKET="$(jq -r '.Stacks[0].Outputs[] | select(.OutputKey=="WebHostingBucketName") | .OutputValue' <<< "${STACK_JSON}")"
APP_URL_DNS="$(jq -r '.Stacks[0].Outputs[] | select(.OutputKey=="AppUrlDns") | .OutputValue' <<< "${STACK_JSON}")"
APP_URL_CF="$(jq -r '.Stacks[0].Outputs[] | select(.OutputKey=="AppUrlCloudFront") | .OutputValue' <<< "${STACK_JSON}")"

[[ -n "${WEB_BUCKET}" && "${WEB_BUCKET}" != "null" ]] || abort "WebHostingBucketName output not found."

TARGET_URL="${APP_URL_DNS}"
if [[ -z "${TARGET_URL}" || "${TARGET_URL}" == "null" ]]; then
  TARGET_URL="${APP_URL_CF}"
fi
[[ -n "${TARGET_URL}" && "${TARGET_URL}" != "null" ]] || abort "No frontend URL output found (AppUrlDns/AppUrlCloudFront)."

UTC_NOW="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

log "Generating test index file: ${WORK_FILE}"
cat > "${WORK_FILE}" <<EOF
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>4-ita Infra Test Page</title>
    <style>
      body { font-family: sans-serif; max-width: 760px; margin: 3rem auto; padding: 0 1rem; line-height: 1.5; }
      .box { border: 1px solid #ddd; border-radius: 8px; padding: 1rem; background: #fafafa; }
      code { background: #eee; padding: 0.15rem 0.35rem; border-radius: 4px; }
    </style>
  </head>
  <body>
    <h1>4-ita Infrastructure Test Page</h1>
    <p>This page was generated and deployed by <code>deploy_test_index.sh</code>.</p>
    <div class="box">
      <p><strong>UTC deployed at:</strong> ${UTC_NOW}</p>
      <p><strong>Stack:</strong> ${STACK_NAME}</p>
      <p><strong>Bucket:</strong> ${WEB_BUCKET}</p>
      <p><strong>Region:</strong> ${AWS_REGION}</p>
    </div>
  </body>
</html>
EOF

log "Uploading test index to s3://${WEB_BUCKET}/index.html"
aws s3 cp "${WORK_FILE}" "s3://${WEB_BUCKET}/index.html" \
  --profile "${AWS_PROFILE}" \
  --region "${AWS_REGION}" \
  --content-type "text/html; charset=utf-8" \
  --cache-control "no-store" \
  --no-progress \
  --no-cli-pager >/dev/null

log "Upload complete."
log "Fetching deployed page via curl: ${TARGET_URL}"
log "HTTP response headers:"
curl -sS -D - -o "${BODY_FILE}" "${TARGET_URL}" | sed 's/^/[deploy_test_index][header] /'

log "First lines of response body:"
head -n 20 "${BODY_FILE}" | sed 's/^/[deploy_test_index][body] /'
log "Test index deployment flow finished."
