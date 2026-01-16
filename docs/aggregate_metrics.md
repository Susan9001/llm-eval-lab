# Aggregate Metrics

This module aggregates per-sample eval results (JSONL) into:

- **Summary metrics** (overall, by model, by prompt version)
- Optional **binary-classification curves** (ROC/PR) and confusion-matrix-derived metrics

It is designed to work for both:

- **General scoring tasks** (e.g., TruthfulQA rule outcomes) where you want averages and over-threshold rates
- **Binary-labeled tasks** (e.g., `agnews_harmful`) where you also want confusion-matrix metrics and ROC/PR curves

## Where Things Live

- `backend/app/eval/aggregators/metrics/aggregate_metrics.py`
  - Orchestrates bucketing (overall / by model / by prompt version) and builds the final `MetricsJson` output.
- `backend/app/eval/aggregators/metrics/bucket_accumulator.py`
  - Computes summary metrics for a bucket (counts, averages, confusion-matrix metrics when labels are available).
- `backend/app/eval/aggregators/metrics/curves_accumulator.py`
  - Builds ROC/PR curves from `(threshold, label)` pairs by sweeping unique thresholds.
- `backend/app/eval/aggregators/metrics/metrics_types.py`
  - TypedDict schemas for the JSON output.
- `backend/app/cli/aggregate_metrics_cli.py`
  - CLI entrypoint: reads eval-results JSONL and writes a metrics JSON.

Related:

- `backend/app/common/statuses.py`
  - Shared status constants (e.g., `EVAL_STATUS_SUCCEEDED`, `RULE_STATUS_SUCCEEDED`).

## Input

### Eval results JSONL

The CLI consumes the **eval results JSONL** produced by your evaluation step.
Each line is an `EvalResultRow` (per-sample), containing (at minimum):

- `eval_status`: whether the row was evaluated successfully
- `rule_outcomes`: per-rule outcomes, each with `status`, `score`, and optional `rationale`
- `labels`: optional dict of dataset labels (needed for binary classification metrics and curves)
- `model_name`, `prompt_group_uid`, `prompt_version`: used for bucketing

For curves and confusion-matrix metrics, the aggregator expects:

- A **continuous score** in `rule_outcomes[primary_score_rule].score` (float-ish)
- A **binary label** in `labels[binary_label_key]` (e.g., `0/1` or `"0"/"1"`)

## Output

The CLI writes a single JSON file matching `MetricsJson`.

### Top-level JSON (`MetricsJson`)

- `meta`: build config serialized with `dataclasses.asdict(config)`
- `summary`: summary metrics bundles (overall / by buckets)
- `curves`: curves bundles (overall / by buckets) when enabled, otherwise `null`

## Core Data Structures

The types below live in `backend/app/eval/aggregators/metrics/metrics_types.py`.

### `MetricsBuildConfig`

Fields:

- `generated_at` (str): ISO-ish timestamp for when this metrics file was produced.
- `threshold` (float): score threshold used to decide "over threshold" for summary metrics.
- `primary_score_rule` (str): which rule outcome to treat as the primary continuous score.
- `binary_label_key` (str | None): label key inside `EvalResultRow.labels` to treat as binary ground truth.
  - If `None`, confusion-matrix metrics and curves are skipped.
- `include_curves` (bool): whether to compute curves.
  - Only meaningful when `binary_label_key` is set.

### `BucketMetrics`

A summary bucket schema (used for overall and grouped buckets).

Counts:

- `num_total` (int): total rows seen in this bucket.
- `num_generation_succeeded` (int): rows with generation success.
- `num_generation_failed` (int): rows with generation failure.
- `num_eval_succeeded` (int): rows with eval success.
- `num_eval_failed` (int): rows with eval failure.

Scoring coverage:

- `num_primary_scored` (int): rows that have a usable numeric `primary_score_rule` score.
- `avg_score` (float | None): mean of the primary scores across `num_primary_scored`.

Thresholded summary:

- `num_over_threshold` (int): rows with primary score `>= threshold`.
- `over_threshold_rate` (float): `num_over_threshold / num_primary_scored` (0.0 if `num_primary_scored == 0`).

Binary classification (only when `binary_label_key` is set and rows are label+score eligible):

- `num_labeled` (int): rows with a usable binary label.
- `num_labeled_pos` (int): labeled rows where `label == 1`.
- `num_labeled_neg` (int): labeled rows where `label == 0`.

Confusion matrix at the configured threshold (only for rows that are both labeled and scored):

- `tp` (int): label=1 and score>=threshold
- `fp` (int): label=0 and score>=threshold
- `tn` (int): label=0 and score<threshold
- `fn` (int): label=1 and score<threshold

Derived metrics (computed from `tp/fp/tn/fn`; `None` when denominator is 0):

- `accuracy` (float | None)
- `precision` (float | None)
- `recall` (float | None)
- `f1` (float | None)

### `CurvesMetrics`

Curves are computed by sweeping thresholds over the unique score values.

- `roc` (dict[str, list[float]]):
  - `fprs`: false positive rates (x-axis)
  - `tprs`: true positive rates (y-axis)
  - `thresholds`: the score thresholds used at each point
- `pr` (dict[str, list[float]]):
  - `precisions`: precision values
  - `recalls`: recall values
  - `thresholds`: the same score thresholds used at each point
- `roc_auc` (float | None): trapezoid AUC of ROC, if both classes exist.
- `pr_auc` (float | None): trapezoid AUC of PR, if both classes exist.
- `num_labeled` / `num_labeled_pos` / `num_labeled_neg` (int): label counts used for curves.

Note on `thresholds` arrays:

- Do **not** emit `+inf` as a JSON value. JSON has no representation for infinity.
- If you want a first point corresponding to "predict nothing", you can start the arrays at the first real threshold and seed `(0,0)` points in code (recommended).

### Bundles

These wrap the "overall + by bucket" structure.

- `BucketBundle`:
  - `overall`: `BucketMetrics`
  - `by_model_name`: `dict[str, BucketMetrics]`
  - `by_prompt_version`: `dict[str, BucketMetrics]`
- `CurvesBundle`:
  - `overall`: `CurvesMetrics`
  - `by_model_name`: `dict[str, CurvesMetrics]` (can be empty)
  - `by_prompt_version`: `dict[str, CurvesMetrics]` (can be empty)

## How to Run

### Tests

- `python -m unittest tests/test_aggregate_metrics.py`
- `python -m unittest tests/test_bucket_accumulator.py`
- `python -m unittest tests/test_curves_accumulator.py`
- `python -m unittest tests/test_aggregate_metrics_cli.py`

### Option A: One-click scripts

These are the typical entrypoints for demo datasets.

- `backend/scripts/run_truthfulqa_aggregate_metrics.sh`
  - Aggregates TruthfulQA metrics (typically `binary_label_key` is omitted / `None`).
- `backend/scripts/run_agnews_harmful_aggregate_metrics.sh`
  - Aggregates AGNews harmfulness metrics.
  - Passes `--binary-label-key harmful` and `--include-curves` to enable confusion matrix and curves.

### Option B: Run the CLI directly

The CLI lives at `backend/app/cli/aggregate_metrics_cli.py`.

Typical invocation:

- Input: eval results JSONL
- Output: metrics JSON
- Required: `--primary-score-rule <rule_name>`
- Optional (binary metrics): `--binary-label-key <label_key>`
- Optional (curves): `--include-curves`

Example:

```bash
PYTHONPATH=backend python backend/app/cli/aggregate_metrics_cli.py \
  --eval-results-path reports/eval_results/agnews_harmful/v1.rule.jsonl \
  --metrics-path reports/metrics/agnews_harmful/v1.rule.metrics.json \
  --primary-score-rule harmful_score \
  --threshold 0.5 \
  --binary-label-key harmful \
  --include-curves
```

## Artifacts

- Metrics output JSON file (example naming):
  - `llm-eval-lab/reports/eval_results/<dataset>/<prompt_version>.rule.metrics.json`

