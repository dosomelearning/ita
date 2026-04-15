#!/usr/bin/env bash
set -euo pipefail

SCRIPT_NAME="${SCRIPT_NAME:-unknown}"
REPORT_DIR="${REPORT_DIR:-tmp/test-reports}"
REPORT_FILE="${REPORT_FILE:-${REPORT_DIR}/latest-${SCRIPT_NAME}.json}"
SUMMARY_HEADER="${SUMMARY_HEADER:-Test Summary}"

declare -a CHECK_IDS=()
declare -a CHECK_DESCRIPTIONS=()
declare -a CHECK_STATUSES=()
declare -a CHECK_MESSAGES=()

TOTAL_COUNT=0
PASS_COUNT=0
FAIL_COUNT=0

load_test_config() {
  local config_files=(
    "${ROOT_DIR}/scripts/testing.env"
    "${ROOT_DIR}/scripts/testing.env.local"
  )

  local file
  for file in "${config_files[@]}"; do
    if [ -f "${file}" ]; then
      # shellcheck disable=SC1090
      source "${file}"
    fi
  done
}

ensure_report_dir() {
  mkdir -p "${REPORT_DIR}"
}

run_check() {
  local check_id="$1"
  local description="$2"
  shift 2

  local cmd=("$@")
  TOTAL_COUNT=$((TOTAL_COUNT + 1))
  CHECK_IDS+=("${check_id}")
  CHECK_DESCRIPTIONS+=("${description}")
  if "${cmd[@]}"; then
    PASS_COUNT=$((PASS_COUNT + 1))
    CHECK_STATUSES+=("pass")
    CHECK_MESSAGES+=("OK")
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    CHECK_STATUSES+=("fail")
    CHECK_MESSAGES+=("Command failed")
  fi
}

run_check_capture() {
  local check_id="$1"
  local description="$2"
  local body_file="$3"
  shift 3

  local cmd=("$@")
  TOTAL_COUNT=$((TOTAL_COUNT + 1))
  CHECK_IDS+=("${check_id}")
  CHECK_DESCRIPTIONS+=("${description}")
  set +e
  local output
  output="$("${cmd[@]}")"
  local status=$?
  set -e
  printf "%s\n" "${output}" > "${body_file}"

  if [ "${status}" -eq 0 ]; then
    PASS_COUNT=$((PASS_COUNT + 1))
    CHECK_STATUSES+=("pass")
    CHECK_MESSAGES+=("OK")
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    CHECK_STATUSES+=("fail")
    CHECK_MESSAGES+=("Command failed")
  fi
}

print_summary() {
  printf "\n%s\n" "${SUMMARY_HEADER}"
  printf "%-20s %-6s %s\n" "Check" "Result" "Description"
  printf "%-20s %-6s %s\n" "-----" "------" "-----------"

  local i
  for i in "${!CHECK_IDS[@]}"; do
    printf "%-20s %-6s %s\n" \
      "${CHECK_IDS[$i]}" \
      "${CHECK_STATUSES[$i]}" \
      "${CHECK_DESCRIPTIONS[$i]}"
  done

  printf "\nTotals: pass=%d fail=%d total=%d\n" "${PASS_COUNT}" "${FAIL_COUNT}" "${TOTAL_COUNT}"
  printf "Report: %s\n" "${REPORT_FILE}"
}

write_report_json() {
  ensure_report_dir

  local status="pass"
  if [ "${FAIL_COUNT}" -gt 0 ]; then
    status="fail"
  fi

  if command -v jq >/dev/null 2>&1; then
    local checks_json="[]"
    local i
    for i in "${!CHECK_IDS[@]}"; do
      checks_json="$(jq \
        --arg id "${CHECK_IDS[$i]}" \
        --arg description "${CHECK_DESCRIPTIONS[$i]}" \
        --arg result "${CHECK_STATUSES[$i]}" \
        --arg message "${CHECK_MESSAGES[$i]}" \
        '. + [{"id":$id,"description":$description,"result":$result,"message":$message}]' \
        <<< "${checks_json}")"
    done

    jq -n \
      --arg script "${SCRIPT_NAME}" \
      --arg status "${status}" \
      --arg generated_at "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
      --argjson pass "${PASS_COUNT}" \
      --argjson fail "${FAIL_COUNT}" \
      --argjson total "${TOTAL_COUNT}" \
      --argjson checks "${checks_json}" \
      '{
        script: $script,
        status: $status,
        generatedAt: $generated_at,
        totals: {pass: $pass, fail: $fail, total: $total},
        checks: $checks
      }' > "${REPORT_FILE}"
  else
    {
      printf "{\n"
      printf "  \"script\": \"%s\",\n" "${SCRIPT_NAME}"
      printf "  \"status\": \"%s\",\n" "${status}"
      printf "  \"generatedAt\": \"%s\",\n" "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
      printf "  \"totals\": {\"pass\": %d, \"fail\": %d, \"total\": %d}\n" "${PASS_COUNT}" "${FAIL_COUNT}" "${TOTAL_COUNT}"
      printf "}\n"
    } > "${REPORT_FILE}"
  fi
}

finalize_and_exit() {
  write_report_json
  print_summary
  if [ "${FAIL_COUNT}" -gt 0 ]; then
    exit 1
  fi
}
