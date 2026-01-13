#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"

# Input: rendered prompts (from day4)
RENDERED_PROMPTS_JSONL_PATH="${ROOT_DIR}/reports/rendered_prompts/truthfulqa_generation_base/v1.jsonl"

# Output: model outputs (day5)
OUT_JSONL_PATH="${ROOT_DIR}/reports/model_outputs/truthfulqa_generation_base/v1.jsonl"

GEN_SCRIPT="${BACKEND_DIR}/app/cli/generate_model_outputs_cli.py"

# Default generation params JSON (override by passing --generation-params-json ...)
GENERATION_PARAMS_JSON='{"temperature":0,"max_tokens":256}'

if [[ ! -f "${RENDERED_PROMPTS_JSONL_PATH}" ]]; then
  echo "Error: rendered prompts not found: ${RENDERED_PROMPTS_JSONL_PATH}"
  exit 1
fi

export PYTHONPATH="${BACKEND_DIR}"

ARGS=(
  "--rendered-prompts-jsonl-path" "${RENDERED_PROMPTS_JSONL_PATH}"
  "--out-jsonl-path" "${OUT_JSONL_PATH}"
  "--provider" "mock"
  "--model-name" "mock-model"
  "--generation-params-json" "${GENERATION_PARAMS_JSON}"
)

# Extra arguments, e.g. --preview-n 3, or override generation params by passing
#   --generation-params-json '{"temperature":1,"max_tokens":64}'
ARGS+=("$@")

python "${GEN_SCRIPT}" "${ARGS[@]}"
echo "Wrote model outputs to: ${OUT_JSONL_PATH}"
