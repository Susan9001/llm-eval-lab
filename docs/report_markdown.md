# Report Markdown

This module generates a readable Markdown report for a single evaluation run. The report is meant for quick review of:

- Run configuration and provenance.
- Aggregated metrics.
- Representative samples (top low score, top high score, near threshold).

Key principle: **MetricsJson is the single source of truth for metrics metadata and metric values.** The report layer renders MetricsJson directly and avoids duplicating fields that already exist in MetricsJson.

## Where Things Live

- `backend/app/report/report_types.py`
  - Report specific TypedDicts that describe the output blocks.
- `backend/app/report/extract.py`
  - Extraction logic for non metrics sections.
  - Builds:
    - A: `RunInfoSection` from snapshot meta and the first eval result row.
    - D: `TopSamplesSection` from eval results using `primary_score_rule` and `threshold` from `metrics_json.meta`.
- `backend/app/report/render_markdown.py`
  - Markdown rendering logic.
  - Renders `RunInfoSection`, `MetricsJson`, and `TopSamplesSection` into a single markdown string.
- `backend/app/cli/report_markdown_cli.py`
  - CLI entry point.
  - Reads input files, wires extract and render, then writes the markdown report.
- `backend/tests/test_render_markdown.py`
  - Golden snapshot test.
  - `EXPECTED_MARKDOWN` is intentionally readable so the formatting style is obvious.
- `backend/scripts/run_agnews_harmful_report_markdown.sh`
  - One click script for AGNews harmful.
- `backend/scripts/run_truthfulqa_report_markdown.sh`
  - One click script for TruthfulQA.

## Input

Report generation requires three input artifacts:

1. **Dataset snapshot metadata JSON**
   - Example: `data/snapshots/dataset_snapshot_agnews_harmful.json`
   - Used for dataset identity and snapshot provenance in **Run Info**.

2. **Aggregated metrics JSON (MetricsJson)**
   - Example: `reports/metrics/<dataset>/v1.rule.metrics.json`
   - Used for the **Metrics** section.
   - Also provides:
     - `metrics_json.meta.primary_score_rule` as the score source for Top lists.
     - `metrics_json.meta.threshold` as the reference for the near threshold list.

3. **Eval results JSONL**
   - Example: `reports/eval_results/<dataset>/v1.rule.jsonl`
   - Used for:
     - The first row, to capture `provider`, `model_name`, `judge_*`, `prompt_*` in **Run Info**.
     - Scanning all rows to build **Top Samples** lists.

## Output

The output is a Markdown report file.

- Example: `reports/reports/<dataset>/v1.rule.md`

The report includes:

- **Run Info**
- **Metrics** (rendered directly from MetricsJson)
- **Top Samples**

## Core Data Structure

All report structures live in `backend/app/report/report_types.py`.

### RunInfoSection

Purpose: capture the run level metadata that is not already owned by MetricsJson.

Sources:

- Snapshot fields come from `DatasetSnapshotMeta` (snapshot meta JSON).
- Prompt, model, and judge fields come from the first `EvalResultRow` in eval results JSONL.

Important rule:

- Do not duplicate any field that exists in `MetricsJson.meta`.

### TopSamplesSection

Purpose: capture representative sample lists.

Fields:

- `k_low`, `k_high`, `k_near`
- `top_low_score`, `top_high_score`, `near_threshold`

Important rules:

- Each list has its own k.
- If k is 0, the list is just empty.
- `near_threshold` is empty when `threshold` is missing.
- Do not store `primary_score_rule` or `threshold` in this section. Those belong to `MetricsJson.meta`.

### SampleScoreItem

Each Top list item keeps only three columns:

- `source_sample_id`
- `score`
- `rationale`

Extraction rule:

- Score and rationale are taken from `eval_result_row.rule_outcomes[primary_score_rule]`.
- Only outcomes with `status == RULE_STATUS_SUCCEEDED` are considered.

## How to Run

### Tests

A golden snapshot test is provided:

- Option A: run directly

```bash
PYTHONPATH=backend python backend/tests/test_render_markdown.py
```

- Option B: run with pytest if you prefer

```bash
PYTHONPATH=backend pytest backend/tests/test_render_markdown.py
```

### Option A: One click script

Prerequisites:

- You have already generated eval results and aggregated metrics for the dataset.

Scripts:

- `backend/scripts/run_agnews_harmful_report_markdown.sh`
- `backend/scripts/run_truthfulqa_report_markdown.sh`

The scripts support overrides via environment variables and optional CLI args.

### Option B: Run the CLI directly

CLI:

- `backend/app/cli/report_markdown_cli.py`

Example:

```bash
PYTHONPATH=backend python backend/app/cli/report_markdown_cli.py \
  --snapshot-meta-path data/snapshots/dataset_snapshot_agnews_harmful.json \
  --metrics-path reports/metrics/agnews_harmful/v1.rule.metrics.json \
  --eval-results-path reports/eval_results/agnews_harmful/v1.rule.jsonl \
  --report-path reports/reports/agnews_harmful/v1.rule.md \
  --title "AG News Harmful Report" \
  --k-low 10 --k-high 10 --k-near 10 \
  --rationale-max-len 120
```

Args:

- `--snapshot-meta-path` (required)
- `--metrics-path` (required)
- `--eval-results-path` (required)
- `--report-path` (required)
- `--title` (optional)
- `--k-low`, `--k-high`, `--k-near` (optional, defaults to 10)
- `--rationale-max-len` (optional, default 120)

## Artifacts

This report is an additional artifact derived from existing artifacts:

- Snapshot meta JSON
- Eval results JSONL
- MetricsJson

The report itself is written to:

- `reports/reports/<dataset>/v1.rule.md`

