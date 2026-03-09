#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_DIR}"

if ! command -v npm >/dev/null 2>&1; then
  echo "[deploy_spa] npm is not available on PATH."
  exit 1
fi

if ! command -v aws >/dev/null 2>&1; then
  echo "[deploy_spa] aws CLI is not available on PATH."
  exit 1
fi

AWS_PROFILE="${AWS_PROFILE:-dev}"
AWS_REGION="${AWS_REGION:-eu-central-1}"
INFRA_STACK_NAME="${INFRA_STACK_NAME:-ita-infra}"
WEB_BUCKET="${WEB_BUCKET:-ita-web-pxuzz47kqx}"
DISTRIBUTION_ID="${DISTRIBUTION_ID:-}"

if [[ -z "${DISTRIBUTION_ID}" ]]; then
  DISTRIBUTION_ID="$(
    AWS_CLI_AUTO_PROMPT=off AWS_PAGER="" AWS_EC2_METADATA_DISABLED=true \
      aws cloudformation describe-stacks \
      --stack-name "${INFRA_STACK_NAME}" \
      --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue | [0]" \
      --output text \
      --profile "${AWS_PROFILE}" \
      --region "${AWS_REGION}" \
      --no-cli-pager
  )"
fi

echo "[deploy_spa] Building SPA assets..."
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
