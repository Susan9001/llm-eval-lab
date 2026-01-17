#!/usr/bin/env bash
# One-click markdown report generator for TruthfulQA.
# Prereqs:
#   1) run_truthfulqa_eval.sh
#   2) run_truthfulqa_aggregate_metrics.sh
#
# Usage:
#   bash backend/scripts/run_truthfulqa_report_markdown.sh
#   K_LOW=10 K_HIGH=10 K_NEAR=0 bash backend/scripts/run_truthfulqa_report_markdown.sh
#   bash backend/scripts/run_truthfulqa_report_markdown.sh --k-near 0

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"

DATASET_DIR="truthfulqa_generation_base"

SNAPSHOT_META_PATH="${ROOT_DIR}/data/snapshots/dataset_snapshot.json"
METRICS_JSON="${ROOT_DIR}/reports/metrics/${DATASET_DIR}/v1.rule.metrics.json"
EVAL_RESULTS_JSONL="${ROOT_DIR}/reports/eval_results/${DATASET_DIR}/v1.rule.jsonl"

OUT_DIR="${ROOT_DIR}/reports/reports/${DATASET_DIR}"
REPORT_PATH="${OUT_DIR}/v1.rule.md"

REPORT_SCRIPT="${BACKEND_DIR}/app/cli/report_markdown_cli.py"

TITLE="${TITLE:-TruthfulQA Report}"
K_LOW="${K_LOW:-10}"
K_HIGH="${K_HIGH:-10}"
K_NEAR="${K_NEAR:-10}"
RATIONALE_MAX_LEN="${RATIONALE_MAX_LEN:-120}"

if [[ ! -f "${SNAPSHOT_META_PATH}" ]]; then
  echo "Error: snapshot meta not found: ${SNAPSHOT_META_PATH}"
  echo "Hint: run backend/scripts/run_truthfulqa_snapshot.sh first."
  exit 1
fi

if [[ ! -f "${METRICS_JSON}" ]]; then
  echo "Error: metrics json not found: ${METRICS_JSON}"
  echo "Hint: run backend/scripts/run_truthfulqa_aggregate_metrics.sh first."
  exit 1
fi

if [[ ! -f "${EVAL_RESULTS_JSONL}" ]]; then
  echo "Error: eval results jsonl not found: ${EVAL_RESULTS_JSONL}"
  echo "Hint: run backend/scripts/run_truthfulqa_eval.sh first."
  exit 1
fi

if [[ ! -f "${REPORT_SCRIPT}" ]]; then
  echo "Error: report CLI script not found: ${REPORT_SCRIPT}"
  exit 1
fi

mkdir -p "${OUT_DIR}"
export PYTHONPATH="${BACKEND_DIR}"

ARGS=(
  "--snapshot-meta-path" "${SNAPSHOT_META_PATH}"
  "--metrics-path" "${METRICS_JSON}"
  "--eval-results-path" "${EVAL_RESULTS_JSONL}"
  "--report-path" "${REPORT_PATH}"
  "--title" "${TITLE}"
  "--k-low" "${K_LOW}"
  "--k-high" "${K_HIGH}"
  "--k-near" "${K_NEAR}"
  "--rationale-max-len" "${RATIONALE_MAX_LEN}"
)

ARGS+=("$@")

echo "Snapshot meta: ${SNAPSHOT_META_PATH}"
echo "Metrics: ${METRICS_JSON}"
echo "Eval results: ${EVAL_RESULTS_JSONL}"
echo "Report: ${REPORT_PATH}"

python "${REPORT_SCRIPT}" "${ARGS[@]}"

echo "Done. Report written to: ${REPORT_PATH}"
