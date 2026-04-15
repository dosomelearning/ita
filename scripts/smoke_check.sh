#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
source "${ROOT_DIR}/scripts/_test_lib.sh"
load_test_config

TIER="all"

usage() {
  cat <<'EOF'
Usage: ./scripts/smoke_check.sh [--tier local|live-basic|live-e2e|all]
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --tier)
      TIER="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      usage
      exit 2
      ;;
  esac
done

case "${TIER}" in
  local)
    ./scripts/test_local.sh
    ;;
  live-basic)
    ./scripts/test_live_basic.sh
    ;;
  live-e2e)
    ./scripts/test_live_e2e.sh
    ;;
  all)
    ./scripts/test_local.sh
    ./scripts/test_live_basic.sh
    if [ -n "${SMOKE_CLASS_PASSWORD:-}" ]; then
      ./scripts/test_live_e2e.sh
    else
      echo "Skipping live-e2e in --tier all: SMOKE_CLASS_PASSWORD is not set."
    fi
    ;;
  *)
    echo "Invalid tier: ${TIER}"
    usage
    exit 2
    ;;
esac
