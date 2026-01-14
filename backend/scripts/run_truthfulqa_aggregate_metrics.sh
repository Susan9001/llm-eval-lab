#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

EVAL_RESULTS_PATH="${ROOT_DIR}/reports/eval_results/truthfulqa_generation_base/v1.rule.jsonl"
METRICS_PATH="${ROOT_DIR}/reports/metrics/truthfulqa_generation_base/v1.rule.metrics.json"
PRIMARY_SCORE_RULE="${PRIMARY_SCORE_RULE:-non_empty_output}"
THRESHOLD="${THRESHOLD:-0.5}"

echo "Eval results: ${EVAL_RESULTS_PATH}"
echo "Primary score rule: ${PRIMARY_SCORE_RULE}"
echo "Threshold: ${THRESHOLD}"

cd "${BACKEND_DIR}"

python -m app.cli.aggregate_metrics_cli \
  --eval-results-path "${EVAL_RESULTS_PATH}" \
  --metrics-path "${METRICS_PATH}" \
  --primary-score-rule "${PRIMARY_SCORE_RULE}" \
  --threshold "${THRESHOLD}"

echo "Done. Aggregated metrics written to: ${METRICS_PATH}"