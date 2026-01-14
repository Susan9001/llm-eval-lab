#!/usr/bin/env bash
# One-click eval runner for TruthfulQA.
# Prereqs:
#   1) run_truthfulqa_snapshot.sh
#   2) run_truthfulqa_rendered_prompts.sh
#   3) run_truthfulqa_model_outputs.sh (or generate model outputs by CLI)
#
# Usage:
#   bash backend/scripts/run_truthfulqa_eval.sh
#   bash backend/scripts/run_truthfulqa_eval.sh --eval-results-path /tmp/eval_results.jsonl

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"

RENDERED_PROMPTS_JSONL="${ROOT_DIR}/reports/rendered_prompts/truthfulqa_generation_base/v1.jsonl"
MODEL_OUTPUTS_JSONL="${ROOT_DIR}/reports/model_outputs/truthfulqa_generation_base/v1.jsonl"

OUT_DIR="${ROOT_DIR}/reports/eval_results/truthfulqa_generation_base"
EVAL_RESULTS_JSONL="${OUT_DIR}/v1.rule.jsonl"

# Comma-separated rule names.
RULE_NAMES="non_empty_output,exact_match_reference"

# Today: only "rule" is expected to work. Keep "llm" for future extensibility.
JUDGE_TYPE="rule"

# Placeholder only, not used by rule judge today.
JUDGE_MODEL_NAME="placeholder"

EVAL_SCRIPT="${BACKEND_DIR}/app/cli/run_eval_cli.py"

if [[ ! -f "${RENDERED_PROMPTS_JSONL}" ]]; then
  echo "Error: rendered prompts jsonl not found: ${RENDERED_PROMPTS_JSONL}"
  echo "Hint: run backend/scripts/run_truthfulqa_rendered_prompts.sh first."
  exit 1
fi

if [[ ! -f "${MODEL_OUTPUTS_JSONL}" ]]; then
  echo "Error: model outputs jsonl not found: ${MODEL_OUTPUTS_JSONL}"
  echo "Hint: run your model outputs script or generate_model_outputs_cli.py first."
  exit 1
fi

if [[ ! -f "${EVAL_SCRIPT}" ]]; then
  echo "Error: eval CLI script not found: ${EVAL_SCRIPT}"
  echo "Hint: if your CLI filename differs, update EVAL_SCRIPT in this .sh file."
  exit 1
fi

mkdir -p "${OUT_DIR}"

export PYTHONPATH="${BACKEND_DIR}"

ARGS=(
  "--model-outputs-path" "${MODEL_OUTPUTS_JSONL}"
  "--rendered-prompts-path" "${RENDERED_PROMPTS_JSONL}"
  "--eval-results-path" "${EVAL_RESULTS_JSONL}"
  "--rule-names" "${RULE_NAMES}"
  "--judge-type" "${JUDGE_TYPE}"
  "--judge-model-name" "${JUDGE_MODEL_NAME}"
)

python "${EVAL_SCRIPT}" "${ARGS[@]}" "$@"

echo "Done. Eval results written to: ${EVAL_RESULTS_JSONL}"
