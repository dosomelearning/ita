#!/usr/bin/env bash
set -euo pipefail

STACK_NAME="${1:-}"
if [[ -z "${STACK_NAME}" ]]; then
  printf 'Usage: %s <stack-name>\n' "$(basename "$0")" >&2
  exit 1
fi

AWS_PROFILE="${AWS_PROFILE:-dev}"
AWS_REGION="${AWS_REGION:-eu-central-1}"
EVENT_LIMIT="${EVENT_LIMIT:-20}"

export AWS_CLI_AUTO_PROMPT=off
export AWS_PAGER=""
export AWS_EC2_METADATA_DISABLED=true

require_cmd() {
  local name="$1"
  command -v "${name}" >/dev/null 2>&1 || {
    printf '[cfn_stack_report][error] Missing required command: %s\n' "${name}" >&2
    exit 1
  }
}

log() {
  printf '[cfn_stack_report] %s\n' "$*"
}

require_cmd aws
require_cmd jq

describe_payload="$(aws cloudformation describe-stacks \
  --profile "${AWS_PROFILE}" \
  --region "${AWS_REGION}" \
  --stack-name "${STACK_NAME}" \
  --output json \
  --no-cli-pager)"

resources_payload="$(aws cloudformation describe-stack-resources \
  --profile "${AWS_PROFILE}" \
  --region "${AWS_REGION}" \
  --stack-name "${STACK_NAME}" \
  --output json \
  --no-cli-pager)"

events_payload="$(aws cloudformation describe-stack-events \
  --profile "${AWS_PROFILE}" \
  --region "${AWS_REGION}" \
  --stack-name "${STACK_NAME}" \
  --output json \
  --no-cli-pager)"

printf '=== Stack Summary ===\n'
printf '%s\n' "${describe_payload}" | jq -r '
  .Stacks[0] as $s |
  [
    "StackName: \($s.StackName)",
    "StackId: \($s.StackId)",
    "Status: \($s.StackStatus)",
    "Created: \($s.CreationTime)",
    "Updated: \($s.LastUpdatedTime // "-")",
    "Description: \($s.Description // "-")"
  ] | .[]
'

printf '\n=== Stack Outputs ===\n'
printf '%s\n' "${describe_payload}" | jq -r '
  (.Stacks[0].Outputs // []) as $o |
  if ($o | length) == 0 then
    "No outputs."
  else
    "ExportName\tOutputKey\tOutputValue",
    ($o[] | [(.ExportName // "-"), .OutputKey, .OutputValue] | @tsv)
  end
'

printf '\n=== Stack Resources ===\n'
printf '%s\n' "${resources_payload}" | jq -r '
  (.StackResources // []) as $r |
  if ($r | length) == 0 then
    "No resources."
  else
    "LogicalResourceId\tResourceType\tResourceStatus\tPhysicalResourceId",
    ($r[] | [.LogicalResourceId, .ResourceType, .ResourceStatus, (.PhysicalResourceId // "-")] | @tsv)
  end
'

printf '\n=== Recent Stack Events (latest first) ===\n'
printf '%s\n' "${events_payload}" | jq -r --argjson limit "${EVENT_LIMIT}" '
  (.StackEvents // [])[:$limit] as $e |
  if ($e | length) == 0 then
    "No events."
  else
    "Timestamp\tLogicalResourceId\tResourceType\tResourceStatus\tStatusReason",
    ($e[] | [.Timestamp, .LogicalResourceId, .ResourceType, .ResourceStatus, (.ResourceStatusReason // "-")] | @tsv)
  end
'

log "Completed stack report for ${STACK_NAME} (profile=${AWS_PROFILE}, region=${AWS_REGION})."
