#!/usr/bin/env bash
# One-click metrics aggregator for AG News harmful.
# Prereqs:
#   1) run_agnews_harmful_eval.sh
#
# Usage:
#   bash backend/scripts/run_agnews_harmful_aggregate_metrics.sh
#   THRESHOLD=0.7 bash backend/scripts/run_agnews_harmful_aggregate_metrics.sh
#   bash backend/scripts/run_agnews_harmful_aggregate_metrics.sh --threshold 0.8

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"

OUT_DIR="${ROOT_DIR}/reports/metrics/agnews_harmful"
METRICS_JSON="${OUT_DIR}/v1.rule.metrics.json"

EVAL_RESULTS_JSONL="${ROOT_DIR}/reports/eval_results/agnews_harmful/v1.rule.jsonl"

PRIMARY_SCORE_RULE="${PRIMARY_SCORE_RULE:-harmful_score}"
THRESHOLD="${THRESHOLD:-0.5}"

METRICS_SCRIPT="${BACKEND_DIR}/app/cli/aggregate_metrics_cli.py"
BINARY_LABEL_KEY="${BINARY_LABEL_KEY:-harmful}"

if [[ ! -f "${EVAL_RESULTS_JSONL}" ]]; then
  echo "Error: eval results jsonl not found: ${EVAL_RESULTS_JSONL}"
  echo "Hint: run backend/scripts/run_agnews_harmful_eval.sh first."
  exit 1
fi

if [[ ! -f "${METRICS_SCRIPT}" ]]; then
  echo "Error: metrics CLI script not found: ${METRICS_SCRIPT}"
  echo "Hint: if your CLI filename differs, update METRICS_SCRIPT in this .sh file."
  exit 1
fi

mkdir -p "${OUT_DIR}"

export PYTHONPATH="${BACKEND_DIR}"

ARGS=(
  "--eval-results-path" "${EVAL_RESULTS_JSONL}"
  "--metrics-path" "${METRICS_JSON}"
  "--primary-score-rule" "${PRIMARY_SCORE_RULE}"
  "--threshold" "${THRESHOLD}"
  "--binary-label-key" "${BINARY_LABEL_KEY}"
  "--include-curves"
)

echo "Eval results: ${EVAL_RESULTS_JSONL}"
echo "Primary score rule: ${PRIMARY_SCORE_RULE}"
echo "Threshold: ${THRESHOLD}"

python "${METRICS_SCRIPT}" "${ARGS[@]}" "$@"

echo "Done. Aggregated metrics written to: ${METRICS_JSON}"
