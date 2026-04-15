#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

SCRIPT_NAME="test_local"
SUMMARY_HEADER="Local Test Summary"
source "${ROOT_DIR}/scripts/_test_lib.sh"

run_check "ms1-unit" "MS1 unit tests" ./b-ms1-ingress/scripts/run_tests.sh
run_check "ms4-unit" "MS4 unit tests" ./b-ms4-statemgr/scripts/run_tests.sh
run_check "spa-unit" "SPA unit tests" bash -c "cd f-spa && npm test"
run_check "spa-build" "SPA build" bash -c "cd f-spa && npm run build"

finalize_and_exit
