#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"

INPUT_PATH="${ROOT_DIR}/data/TruthfulQA.csv"
OUT_JSONL="${ROOT_DIR}/data/snapshots/mini_truth.jsonl"
META_JSON="${ROOT_DIR}/data/snapshots/dataset_snapshot.json"

BUILD_SCRIPT="${BACKEND_DIR}/app/datasets/build_dataset_snapshot.py"

if [[ ! -f "${INPUT_PATH}" ]]; then
  echo "Error: input not found: ${INPUT_PATH}"
  exit 1
fi

export PYTHONPATH="${BACKEND_DIR}"

ARGS=(
  "--input-path" "${INPUT_PATH}"
  "--format" "csv"
  "--adapter" "truthfulqa"
  "--out-jsonl" "${OUT_JSONL}"
  "--snapshot-meta" "${META_JSON}"
  "--preview-n" "3"
  "--metadata-keys" "Type" "Category" "Source"
  "--dataset-group-uid" "truthfulqa"
  "--dataset-display-name" "TruthfulQA"
  "--split" "test"
)

# 默认 limit=80，你也可以在命令行用 --limit 覆盖它（后面的参数会覆盖前面的）
ARGS+=("--limit" "80")

# 透传用户额外参数：例如 --should-random-sample --seed 42 --limit 50
ARGS+=("$@")

python "${BUILD_SCRIPT}" "${ARGS[@]}"
