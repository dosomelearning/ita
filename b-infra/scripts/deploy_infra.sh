#!/usr/bin/env bash
set -euo pipefail

# Deploy/update b-infra CloudFormation stack using a local JSON parameter file.
# This script does not create parameter files; provide one before running.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

STACK_NAME="${STACK_NAME:-ita-infra}"
AWS_PROFILE="${AWS_PROFILE:-dev}"
AWS_REGION="${AWS_REGION:-eu-central-1}"
TEMPLATE_FILE="${TEMPLATE_FILE:-${MODULE_DIR}/template-infra.yaml}"
PARAMS_FILE="${1:-${MODULE_DIR}/params/dev.parameters.json}"

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

require_file "${TEMPLATE_FILE}"
require_file "${PARAMS_FILE}"

log "Starting deployment flow."
log "Stack name: ${STACK_NAME}"
log "AWS profile: ${AWS_PROFILE}"
log "AWS region: ${AWS_REGION}"
log "Template file: ${TEMPLATE_FILE}"
log "Parameters file: ${PARAMS_FILE}"

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
