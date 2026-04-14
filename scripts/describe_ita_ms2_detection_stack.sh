#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STACK_NAME="${STACK_NAME:-ita-ms2-detection}"

"${SCRIPT_DIR}/cfn_stack_report.sh" "${STACK_NAME}"
