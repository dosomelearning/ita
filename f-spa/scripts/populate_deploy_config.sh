#!/usr/bin/env bash
set -euo pipefail

CALLER_DIR="$(pwd)"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[populate_deploy_config] Required command not found: $1"
    exit 1
  fi
}

require_cmd jq
require_cmd aws

if [[ $# -ne 1 ]]; then
  echo "Usage: ./scripts/populate_deploy_config.sh <config-file>"
  exit 1
fi

CONFIG_INPUT="$1"

if [[ "${CONFIG_INPUT}" = /* ]]; then
  CONFIG_FILE="${CONFIG_INPUT}"
else
  CONFIG_FILE="${CALLER_DIR}/${CONFIG_INPUT}"
fi

if [[ ! -f "${CONFIG_FILE}" ]]; then
  echo "[populate_deploy_config] Config file not found: ${CONFIG_FILE}"
  exit 1
fi

cd "${PROJECT_DIR}"

AWS_PROFILE="$(jq -r '.inputs.awsProfile // empty' "${CONFIG_FILE}")"
AWS_REGION="$(jq -r '.inputs.awsRegion // empty' "${CONFIG_FILE}")"
INFRA_STACK_NAME="$(jq -r '.inputs.infraStackName // empty' "${CONFIG_FILE}")"
MS1_STACK_NAME="$(jq -r '.inputs.ms1StackName // empty' "${CONFIG_FILE}")"
MS4_STACK_NAME="$(jq -r '.inputs.ms4StackName // empty' "${CONFIG_FILE}")"

if [[ -z "${AWS_PROFILE}" || -z "${AWS_REGION}" || -z "${INFRA_STACK_NAME}" || -z "${MS1_STACK_NAME}" || -z "${MS4_STACK_NAME}" ]]; then
  echo "[populate_deploy_config] Config file must define inputs.awsProfile, inputs.awsRegion, inputs.infraStackName, inputs.ms1StackName, and inputs.ms4StackName."
  exit 1
fi

read_stack_output() {
  local stack_name="$1"
  local output_key="$2"

  AWS_CLI_AUTO_PROMPT=off AWS_PAGER="" AWS_EC2_METADATA_DISABLED=true \
    aws cloudformation describe-stacks \
      --stack-name "${stack_name}" \
      --query "Stacks[0].Outputs[?OutputKey=='${output_key}'].OutputValue | [0]" \
      --output text \
      --profile "${AWS_PROFILE}" \
      --region "${AWS_REGION}" \
      --no-cli-pager
}

WEB_BUCKET_NAME="$(read_stack_output "${INFRA_STACK_NAME}" "WebHostingBucketName")"
CLOUDFRONT_DISTRIBUTION_ID="$(read_stack_output "${INFRA_STACK_NAME}" "CloudFrontDistributionId")"
MS1_API_BASE_URL="$(read_stack_output "${MS1_STACK_NAME}" "ApiEndpoint")"
MS4_API_BASE_URL="$(read_stack_output "${MS4_STACK_NAME}" "ApiEndpoint")"

if [[ -z "${WEB_BUCKET_NAME}" || "${WEB_BUCKET_NAME}" == "None" ]]; then
  echo "[populate_deploy_config] Failed to resolve WebHostingBucketName from ${INFRA_STACK_NAME}."
  exit 1
fi

if [[ -z "${CLOUDFRONT_DISTRIBUTION_ID}" || "${CLOUDFRONT_DISTRIBUTION_ID}" == "None" ]]; then
  echo "[populate_deploy_config] Failed to resolve CloudFrontDistributionId from ${INFRA_STACK_NAME}."
  exit 1
fi

if [[ -z "${MS1_API_BASE_URL}" || "${MS1_API_BASE_URL}" == "None" ]]; then
  echo "[populate_deploy_config] Failed to resolve ApiEndpoint from ${MS1_STACK_NAME}."
  exit 1
fi

if [[ -z "${MS4_API_BASE_URL}" || "${MS4_API_BASE_URL}" == "None" ]]; then
  echo "[populate_deploy_config] Failed to resolve ApiEndpoint from ${MS4_STACK_NAME}."
  exit 1
fi

TMP_FILE="$(mktemp)"
trap 'rm -f "${TMP_FILE}"' EXIT

jq \
  --arg web_bucket_name "${WEB_BUCKET_NAME}" \
  --arg cloudfront_distribution_id "${CLOUDFRONT_DISTRIBUTION_ID}" \
  --arg ms1_api_base_url "${MS1_API_BASE_URL}" \
  --arg ms4_api_base_url "${MS4_API_BASE_URL}" \
  '.resolved.webBucketName = $web_bucket_name
   | .resolved.cloudFrontDistributionId = $cloudfront_distribution_id
   | .resolved.ms1ApiBaseUrl = $ms1_api_base_url
   | .resolved.ms4ApiBaseUrl = $ms4_api_base_url' \
  "${CONFIG_FILE}" > "${TMP_FILE}"

mv "${TMP_FILE}" "${CONFIG_FILE}"

echo "[populate_deploy_config] Updated ${CONFIG_FILE}"
echo "[populate_deploy_config] webBucketName=${WEB_BUCKET_NAME}"
echo "[populate_deploy_config] cloudFrontDistributionId=${CLOUDFRONT_DISTRIBUTION_ID}"
echo "[populate_deploy_config] ms1ApiBaseUrl=${MS1_API_BASE_URL}"
echo "[populate_deploy_config] ms4ApiBaseUrl=${MS4_API_BASE_URL}"
