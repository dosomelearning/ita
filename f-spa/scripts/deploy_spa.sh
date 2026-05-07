#!/usr/bin/env bash
set -euo pipefail

CALLER_DIR="$(pwd)"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[deploy_spa] Required command not found: $1"
    exit 1
  fi
}

if [[ $# -ne 1 ]]; then
  echo "Usage: ./scripts/deploy_spa.sh <config-file>"
  exit 1
fi

CONFIG_INPUT="$1"

if [[ "${CONFIG_INPUT}" = /* ]]; then
  CONFIG_FILE="${CONFIG_INPUT}"
else
  CONFIG_FILE="${CALLER_DIR}/${CONFIG_INPUT}"
fi

if [[ ! -f "${CONFIG_FILE}" ]]; then
  echo "[deploy_spa] Config file not found: ${CONFIG_FILE}"
  exit 1
fi

cd "${PROJECT_DIR}"

require_cmd jq
require_cmd npm
require_cmd aws

AWS_PROFILE="$(jq -r '.inputs.awsProfile // empty' "${CONFIG_FILE}")"
AWS_REGION="$(jq -r '.inputs.awsRegion // empty' "${CONFIG_FILE}")"
WEB_BUCKET="$(jq -r '.resolved.webBucketName // empty' "${CONFIG_FILE}")"
DISTRIBUTION_ID="$(jq -r '.resolved.cloudFrontDistributionId // empty' "${CONFIG_FILE}")"
INGRESS_GATEWAY_MODE="$(jq -r '.inputs.ingressGatewayMode // empty' "${CONFIG_FILE}")"
STATE_GATEWAY_MODE="$(jq -r '.inputs.stateGatewayMode // empty' "${CONFIG_FILE}")"
MS1_API_BASE_URL="$(jq -r '.resolved.ms1ApiBaseUrl // empty' "${CONFIG_FILE}")"
MS4_API_BASE_URL="$(jq -r '.resolved.ms4ApiBaseUrl // empty' "${CONFIG_FILE}")"

if [[ -z "${AWS_PROFILE}" || -z "${AWS_REGION}" || -z "${WEB_BUCKET}" || -z "${DISTRIBUTION_ID}" || -z "${INGRESS_GATEWAY_MODE}" || -z "${STATE_GATEWAY_MODE}" || -z "${MS1_API_BASE_URL}" || -z "${MS4_API_BASE_URL}" ]]; then
  echo "[deploy_spa] Config file must define inputs.awsProfile, inputs.awsRegion, inputs.ingressGatewayMode, inputs.stateGatewayMode, and resolved.webBucketName, resolved.cloudFrontDistributionId, resolved.ms1ApiBaseUrl, resolved.ms4ApiBaseUrl."
  echo "[deploy_spa] Populate the config first with ./scripts/populate_deploy_config.sh <config-file>."
  exit 1
fi

echo "[deploy_spa] Building SPA assets..."
VITE_INGRESS_GATEWAY_MODE="${INGRESS_GATEWAY_MODE}" \
VITE_STATE_GATEWAY_MODE="${STATE_GATEWAY_MODE}" \
VITE_MS1_API_BASE_URL="${MS1_API_BASE_URL}" \
VITE_MS4_API_BASE_URL="${MS4_API_BASE_URL}" \
  npm run build

echo "[deploy_spa] Uploading dist/ to s3://${WEB_BUCKET} ..."
AWS_CLI_AUTO_PROMPT=off AWS_PAGER="" AWS_EC2_METADATA_DISABLED=true \
  aws s3 sync dist/ "s3://${WEB_BUCKET}" \
  --profile "${AWS_PROFILE}" \
  --region "${AWS_REGION}" \
  --delete \
  --no-cli-pager

if [[ -n "${DISTRIBUTION_ID}" && "${DISTRIBUTION_ID}" != "None" ]]; then
  echo "[deploy_spa] Creating CloudFront invalidation for distribution ${DISTRIBUTION_ID} ..."
  AWS_CLI_AUTO_PROMPT=off AWS_PAGER="" AWS_EC2_METADATA_DISABLED=true \
    aws cloudfront create-invalidation \
    --distribution-id "${DISTRIBUTION_ID}" \
    --paths "/*" \
    --profile "${AWS_PROFILE}" \
    --no-cli-pager
else
  echo "[deploy_spa] CloudFront distribution ID is unavailable; skipping invalidation."
fi

echo "[deploy_spa] Deployment complete."
