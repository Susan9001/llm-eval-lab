#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"

INPUT_PATH="${ROOT_DIR}/data/agnews_harmful_demo.csv"
OUT_JSONL_PATH="${ROOT_DIR}/data/snapshots/agnews_harmful.jsonl"
SNAPSHOT_META_PATH="${ROOT_DIR}/data/snapshots/dataset_snapshot_agnews_harmful.json"

BUILD_SCRIPT="${BACKEND_DIR}/app/cli/build_dataset_snapshot_cli.py"

if [[ ! -f "${INPUT_PATH}" ]]; then
  echo "Error: input not found: ${INPUT_PATH}"
  exit 1
fi

export PYTHONPATH="${BACKEND_DIR}"

ARGS=(
  "--input-path" "${INPUT_PATH}"
  "--format" "csv"
  "--adapter" "agnews_harmful"
  "--out-jsonl-path" "${OUT_JSONL_PATH}"
  "--snapshot-meta-path" "${SNAPSHOT_META_PATH}"
  "--preview-n" "3"
  "--metadata-keys" "label"
  "--dataset-group-uid" "agnews_harmful"
  "--dataset-display-name" "AG News (harmful 0/1 demo)"
  "--split" "demo"
)

# Extra arguments, e.g. --should-random-sample --seed 42
ARGS+=("$@")

python "${BUILD_SCRIPT}" "${ARGS[@]}"

echo "Wrote dataset snapshot to: ${OUT_JSONL_PATH}"
echo "Wrote snapshot meta to: ${SNAPSHOT_META_PATH}"
