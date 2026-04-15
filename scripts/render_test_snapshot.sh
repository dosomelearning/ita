#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

REPORT_DIR="${REPORT_DIR:-tmp/test-reports}"
OUT_FILE="${1:-docs/testing/latest-manual-run.md}"

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required for snapshot rendering."
  exit 2
fi

REPORT_FILES=(
  "${REPORT_DIR}/latest-test_local.json"
  "${REPORT_DIR}/latest-test_live_basic.json"
  "${REPORT_DIR}/latest-test_live_e2e.json"
)

mkdir -p "$(dirname "${OUT_FILE}")"

{
  echo "# Latest Manual Test Snapshot"
  echo
  echo "- Generated: \`$(date -u +"%Y-%m-%dT%H:%M:%SZ")\`"
  echo "- Source report directory: \`${REPORT_DIR}\`"
  echo
  echo "## Overview"
  echo
  echo "| Runner | Status | Generated At | Pass | Fail | Total |"
  echo "|---|---|---|---:|---:|---:|"

  for report in "${REPORT_FILES[@]}"; do
    runner="$(basename "${report}" .json)"
    if [ -f "${report}" ]; then
      script_name="$(jq -r '.script' "${report}")"
      status="$(jq -r '.status' "${report}")"
      generated_at="$(jq -r '.generatedAt' "${report}")"
      pass_count="$(jq -r '.totals.pass' "${report}")"
      fail_count="$(jq -r '.totals.fail' "${report}")"
      total_count="$(jq -r '.totals.total' "${report}")"
      echo "| ${script_name} | ${status} | ${generated_at} | ${pass_count} | ${fail_count} | ${total_count} |"
    else
      echo "| ${runner} | missing | - | - | - | - |"
    fi
  done

  for report in "${REPORT_FILES[@]}"; do
    if [ ! -f "${report}" ]; then
      continue
    fi

    script_name="$(jq -r '.script' "${report}")"
    generated_at="$(jq -r '.generatedAt' "${report}")"

    echo
    echo "## ${script_name}"
    echo
    echo "- Generated At: \`${generated_at}\`"
    echo
    echo "| Check ID | Result | Description | Message |"
    echo "|---|---|---|---|"
    jq -r '.checks[] | "| \(.id) | \(.result) | \(.description | gsub("\\|"; "\\\\|")) | \(.message | gsub("\\|"; "\\\\|")) |"' "${report}"
  done

  echo
  echo "## Notes"
  echo
  echo "- This file is generated from JSON artifacts under \`${REPORT_DIR}\`."
  echo "- Regenerate using: \`./scripts/render_test_snapshot.sh\`."
} > "${OUT_FILE}"

echo "Snapshot written to ${OUT_FILE}"
