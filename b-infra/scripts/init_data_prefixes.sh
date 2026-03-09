#!/usr/bin/env bash
set -euo pipefail

STACK_NAME="${STACK_NAME:-ita-infra}"
AWS_PROFILE="${AWS_PROFILE:-dev}"
AWS_REGION="${AWS_REGION:-eu-central-1}"

PREFIXES=(
  "uploaded/"
  "processed/"
  "rekognition/"
  "faces/"
)

export AWS_CLI_AUTO_PROMPT=off
export AWS_PAGER=""
export AWS_EC2_METADATA_DISABLED=true

log() {
  printf '[init_data_prefixes] %s\n' "$*"
}

abort() {
  printf '[init_data_prefixes][error] %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || abort "Missing required command: $1"
}

require_cmd aws
require_cmd jq

log "Starting prefix initialization."
log "Stack: ${STACK_NAME}"
log "AWS profile: ${AWS_PROFILE}"
log "AWS region: ${AWS_REGION}"

STACK_JSON="$(aws cloudformation describe-stacks \
  --profile "${AWS_PROFILE}" \
  --region "${AWS_REGION}" \
  --stack-name "${STACK_NAME}" \
  --output json \
  --no-cli-pager)"

DATA_BUCKET="$(jq -r '.Stacks[0].Outputs[] | select(.OutputKey=="SharedProcessingBucketName") | .OutputValue' <<< "${STACK_JSON}")"
[[ -n "${DATA_BUCKET}" && "${DATA_BUCKET}" != "null" ]] || abort "SharedProcessingBucketName output not found."

log "Target data bucket: ${DATA_BUCKET}"

for prefix in "${PREFIXES[@]}"; do
  log "Ensuring prefix marker exists: s3://${DATA_BUCKET}/${prefix}"
  aws s3api put-object \
    --profile "${AWS_PROFILE}" \
    --region "${AWS_REGION}" \
    --bucket "${DATA_BUCKET}" \
    --key "${prefix}" \
    --content-length 0 \
    --no-cli-pager >/dev/null
done

log "Prefix initialization finished successfully."
