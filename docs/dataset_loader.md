# Dataset Loader

This codepath turns raw dataset files (CSV or JSONL) into a standardized list of `SampleRecord`s via a dataset-specific adapter, and supports:

1. Optional, reproducible sampling.
2. Human-friendly previews (metadata preview + sample preview).
3. Writing a dataset snapshot to JSONL, plus a snapshot meta JSON.

## Where Things Live

Recommended layout under `backend/app/datasets/`:

1. `dataset_loader.py`  
   Generic file reading, sampling, adapter dispatch, and preview helpers.
2. `dataset_types.py`  
   Type definitions such as `SampleRecord`, `RawRow`, and `AdapterFn`.
3. `truthfulqa.py`  
   A TruthfulQA adapter implementation (example adapter) under `backend/app/datasets/adapters`.
4. `backend/app/cli/build_dataset_snapshot_cli.py`  
   A CLI entrypoint that produces snapshot artifacts.

## Core Data Structures

### SampleRecord

`SampleRecord` is the adapter output contract:

- `source_sample_id`: Identifier from the source dataset.
- `input_text`: The model input text.
- `reference_output`: Optional reference answer/target.
- `metadata`: Optional dict for extra fields (category, source, difficulty, etc.).

See `dataset_types.py` for the exact type.

### AdapterFn

An adapter is a function:

- Inputs: `row` (a raw row dict), `row_index` (1-based row index from the original file).
- Output: a `SampleRecord`.

Each dataset has its own adapter function. `dataset_loader.get_adapter(adapter_name)` selects the adapter.

## Sampling Rules

Sampling is controlled by `apply_sampling(items, limit, seed, should_random_sample)`.

Rules are intentionally strict to avoid ambiguity:

1. If `should_random_sample=True`, `limit` must be provided; otherwise raise.
2. If `limit is None` and `should_random_sample=False`, keep all rows (no shuffle).
3. If `limit is not None` and `should_random_sample=False`, take the first `limit` rows (no shuffle).
4. If `limit is not None` and `should_random_sample=True`, shuffle (optionally with `seed`) and take the first `limit` rows.

Note: `row_index` is always the original file row index and never changes after shuffle. This keeps `source_sample_id` construction stable and debuggable.

## Inputs

### Raw dataset files

Location: `data/`

Example:

- `data/TruthfulQA.csv`

Format: CSV or JSONL

### Adapter configuration

Specified via `--adapter` argument, e.g., `truthfulqa`

### Sampling parameters

- `--limit`: Optional limit on number of rows.
- `--should-random-sample`: If set, shuffle and sample.
- `--seed`: Random seed for sampling.

## Outputs

Location: `data/snapshots/`

### Snapshot JSONL

- Path: `--out-jsonl`, e.g., `data/snapshots/mini_truth.jsonl`
- Each line: One JSON object corresponding to a `SampleRecord`.

### Snapshot meta JSON

- Path: `--snapshot-meta`, e.g., `data/snapshots/dataset_snapshot.json`
- Contains metadata for traceability and reproducibility.

## How to run

### Option A: One-click script

```bash
bash backend/scripts/run_truthfulqa_rendered_prompts.sh
```
It uses [TruthfulQA.csv](https://github.com/sylinrl/TruthfulQA/blob/main/TruthfulQA.csv) as input.

### Option B: Run the CLI directly

```bash
PYTHONPATH=backend python backend/app/datasets/build_dataset_snapshot_cli.py \
  --input-path data/TruthfulQA.csv \
  --format csv \
  --adapter truthfulqa \
  --out-jsonl data/snapshots/mini_truth.jsonl \
  --snapshot-meta data/snapshots/dataset_snapshot.json \
  --dataset-group-uid truthfulqa \
  --dataset-display-name TruthfulQA \
  --split test \
  --limit 80
```

For random sampling:

```bash
PYTHONPATH=backend python backend/app/datasets/build_dataset_snapshot_cli.py \
  --input-path data/TruthfulQA.csv \
  --format csv \
  --adapter truthfulqa \
  --out-jsonl data/snapshots/mini_truth.jsonl \
  --snapshot-meta data/snapshots/dataset_snapshot.json \
  --dataset-group-uid truthfulqa \
  --dataset-display-name TruthfulQA \
  --split test \
  --limit 80 \
  --should-random-sample \
  --seed 42
```


## Artifacts

1. Dataset version (--dataset-version`)
   - If `--dataset-version` is provided, it is used as-is.
   - Otherwise, a readable version string is auto-generated (date + sampling parameters).
2. Snapshot JSONL (`--out-jsonl`)
   - One JSON object per line, corresponding to one `SampleRecord`.
3. Snapshot meta JSON (`--snapshot-meta`)
   - Records key metadata needed for traceability and reproducibility.

## Adding a New Dataset Adapter

Recommended steps:

1. Create a new file under `backend/app/datasets/`, e.g. `<dataset_name>.py`.
2. Implement `adapt_<dataset_name>_row(row, row_index) -> SampleRecord`.
3. Add a branch in `dataset_loader.get_adapter()` mapping `adapter_name` to the adapter function.
4. Run `build_dataset_snapshot_cli.py` once, inspect previews, then validate the JSONL output.
