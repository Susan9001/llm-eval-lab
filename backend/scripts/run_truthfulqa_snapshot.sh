#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"

INPUT_PATH="${ROOT_DIR}/data/TruthfulQA.csv"
OUT_JSONL="${ROOT_DIR}/data/snapshots/mini_truth.jsonl"
META_JSON="${ROOT_DIR}/data/snapshots/dataset_snapshot.json"

BUILD_SCRIPT="${BACKEND_DIR}/app/cli/build_dataset_snapshot_cli.py"

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

ARGS+=("--limit" "80")

# Extra arguments, e.g. --should-random-sample --seed 42 --limit 50
ARGS+=("$@")

python "${BUILD_SCRIPT}" "${ARGS[@]}"
