#!/usr/bin/env bash
set -euo pipefail

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

usage() {
  cat <<'EOF'
Usage:
  ./b-infra/scripts/init_data_prefixes.sh <environment-config.json>

The config file must contain:
  - stackName
  - awsProfile
  - awsRegion
EOF
}

[[ $# -eq 1 ]] || {
  usage >&2
  abort "Exactly one environment config JSON file is required."
}

require_cmd aws
require_cmd jq

CONFIG_FILE="$1"
[[ -f "${CONFIG_FILE}" ]] || abort "Required file not found: ${CONFIG_FILE}"

STACK_NAME="$(jq -r '.stackName // empty' "${CONFIG_FILE}")"
AWS_PROFILE="$(jq -r '.awsProfile // empty' "${CONFIG_FILE}")"
AWS_REGION="$(jq -r '.awsRegion // empty' "${CONFIG_FILE}")"

[[ -n "${STACK_NAME}" ]] || abort "Missing required config value: stackName"
[[ -n "${AWS_PROFILE}" ]] || abort "Missing required config value: awsProfile"
[[ -n "${AWS_REGION}" ]] || abort "Missing required config value: awsRegion"

log "Starting prefix initialization."
log "Stack: ${STACK_NAME}"
log "AWS profile: ${AWS_PROFILE}"
log "AWS region: ${AWS_REGION}"
log "Config file: ${CONFIG_FILE}"

STACK_JSON="$(aws cloudformation describe-stacks \
  --profile "${AWS_PROFILE}" \
  --region "${AWS_REGION}" \
  --stack-name "${STACK_NAME}" \
  --output json \
  --no-cli-pager)"

STACK_STATUS="$(jq -r '.Stacks[0].StackStatus // empty' <<< "${STACK_JSON}")"
[[ -n "${STACK_STATUS}" ]] || abort "StackStatus not found in CloudFormation response."

case "${STACK_STATUS}" in
  CREATE_COMPLETE|UPDATE_COMPLETE|UPDATE_ROLLBACK_COMPLETE|IMPORT_COMPLETE|IMPORT_ROLLBACK_COMPLETE)
    ;;
  *)
    abort "Stack is not ready for output-dependent actions yet. Current status: ${STACK_STATUS}"
    ;;
esac

DATA_BUCKET="$(jq -r '(.Stacks[0].Outputs // [])[] | select(.OutputKey=="SharedProcessingBucketName") | .OutputValue' <<< "${STACK_JSON}")"
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
