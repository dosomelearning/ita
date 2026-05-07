#!/usr/bin/env bash
set -euo pipefail

# Deploy/update b-infra CloudFormation stack using a mandatory environment descriptor.
# The descriptor contains stack/profile/region settings plus the CloudFormation parameters array.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

export AWS_CLI_AUTO_PROMPT=off
export AWS_PAGER=""
export AWS_EC2_METADATA_DISABLED=true

log() {
  printf '[deploy_infra] %s\n' "$*"
}

abort() {
  printf '[deploy_infra][error] %s\n' "$*" >&2
  exit 1
}

require_file() {
  local path="$1"
  [[ -f "${path}" ]] || abort "Required file not found: ${path}"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || abort "Missing required command: $1"
}

usage() {
  cat <<'EOF'
Usage:
  ./b-infra/scripts/deploy_infra.sh <environment-config.json>

The config file must contain:
  - stackName
  - awsProfile
  - awsRegion
  - parameters (CloudFormation parameter array)

Optional:
  - templateFile
EOF
}

[[ $# -eq 1 ]] || {
  usage >&2
  abort "Exactly one environment config JSON file is required."
}

require_cmd aws
require_cmd jq

CONFIG_FILE="$1"
require_file "${CONFIG_FILE}"

STACK_NAME="$(jq -r '.stackName // empty' "${CONFIG_FILE}")"
AWS_PROFILE="$(jq -r '.awsProfile // empty' "${CONFIG_FILE}")"
AWS_REGION="$(jq -r '.awsRegion // empty' "${CONFIG_FILE}")"
TEMPLATE_VALUE="$(jq -r '.templateFile // empty' "${CONFIG_FILE}")"

[[ -n "${STACK_NAME}" ]] || abort "Missing required config value: stackName"
[[ -n "${AWS_PROFILE}" ]] || abort "Missing required config value: awsProfile"
[[ -n "${AWS_REGION}" ]] || abort "Missing required config value: awsRegion"

if [[ -n "${TEMPLATE_VALUE}" ]]; then
  TEMPLATE_FILE="${TEMPLATE_VALUE}"
else
  TEMPLATE_FILE="${MODULE_DIR}/template-infra.yaml"
fi

require_file "${TEMPLATE_FILE}"

PARAMS_FILE="$(mktemp /tmp/ita-infra-params-XXXXXX.json)"
cleanup() {
  rm -f "${PARAMS_FILE}"
}
trap cleanup EXIT

jq -e '.parameters | arrays' "${CONFIG_FILE}" > "${PARAMS_FILE}" || \
  abort "Config field 'parameters' must be a JSON array."

log "Starting deployment flow."
log "Stack name: ${STACK_NAME}"
log "AWS profile: ${AWS_PROFILE}"
log "AWS region: ${AWS_REGION}"
log "Template file: ${TEMPLATE_FILE}"
log "Config file: ${CONFIG_FILE}"
log "Extracted parameters file: ${PARAMS_FILE}"

STACK_EXISTS=0
STACK_STATUS=""
if STACK_STATUS="$(aws cloudformation describe-stacks \
  --profile "${AWS_PROFILE}" \
  --region "${AWS_REGION}" \
  --stack-name "${STACK_NAME}" \
  --query "Stacks[0].StackStatus" \
  --output text \
  --no-cli-pager 2>/dev/null)"; then
  STACK_EXISTS=1
fi

if [[ "${STACK_EXISTS}" -eq 1 ]]; then
  if [[ "${STACK_STATUS}" == "ROLLBACK_COMPLETE" ]]; then
    log "Stack exists in ROLLBACK_COMPLETE -> deleting before recreate."
    aws cloudformation delete-stack \
      --profile "${AWS_PROFILE}" \
      --region "${AWS_REGION}" \
      --stack-name "${STACK_NAME}" \
      --no-cli-pager
    log "Waiting for stack-delete-complete."
    aws cloudformation wait stack-delete-complete \
      --profile "${AWS_PROFILE}" \
      --region "${AWS_REGION}" \
      --stack-name "${STACK_NAME}" \
      --no-cli-pager
    STACK_EXISTS=0
    log "Rollback stack deleted; proceeding with create-stack."
  fi
fi

if [[ "${STACK_EXISTS}" -eq 1 ]]; then
  log "Stack exists -> running update-stack."
  set +e
  UPDATE_OUTPUT="$(aws cloudformation update-stack \
    --profile "${AWS_PROFILE}" \
    --region "${AWS_REGION}" \
    --stack-name "${STACK_NAME}" \
    --template-body "file://${TEMPLATE_FILE}" \
    --parameters "file://${PARAMS_FILE}" \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --no-cli-pager 2>&1)"
  UPDATE_CODE=$?
  set -e

  if [[ "${UPDATE_CODE}" -ne 0 ]]; then
    if grep -q "No updates are to be performed" <<< "${UPDATE_OUTPUT}"; then
      log "No changes detected. Stack is already up to date."
      exit 0
    fi
    printf '%s\n' "${UPDATE_OUTPUT}" >&2
    abort "update-stack failed."
  fi

  log "Update started; waiting for stack-update-complete."
  aws cloudformation wait stack-update-complete \
    --profile "${AWS_PROFILE}" \
    --region "${AWS_REGION}" \
    --stack-name "${STACK_NAME}" \
    --no-cli-pager
  log "Update completed."
else
  log "Stack not found -> running create-stack."
  aws cloudformation create-stack \
    --profile "${AWS_PROFILE}" \
    --region "${AWS_REGION}" \
    --stack-name "${STACK_NAME}" \
    --template-body "file://${TEMPLATE_FILE}" \
    --parameters "file://${PARAMS_FILE}" \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --no-cli-pager >/dev/null

  log "Create started; waiting for stack-create-complete."
  aws cloudformation wait stack-create-complete \
    --profile "${AWS_PROFILE}" \
    --region "${AWS_REGION}" \
    --stack-name "${STACK_NAME}" \
    --no-cli-pager
  log "Create completed."
fi

log "Fetching stack outputs."
aws cloudformation describe-stacks \
  --profile "${AWS_PROFILE}" \
  --region "${AWS_REGION}" \
  --stack-name "${STACK_NAME}" \
  --query "Stacks[0].Outputs" \
  --output table \
  --no-cli-pager

log "Deployment flow finished successfully."
