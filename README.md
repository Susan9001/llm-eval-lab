# llm-eval-lab

Evaluation lab for LLM quality and safety. Python + FastAPI + PostgreSQL + Redis, build for offline metrics, regression gating, and reporting.

## Tech stack

- Python (backend services)
- PostgreSQL (evaluation metadata and results)
- Redis (caching and task queue)
- Docker and Docker Compose (local orchestration)

## Dependencies

```bash
PYTHONPATH=backend pip install -r backend/requirements-dev.txt
```

## Quickstart

CLIs to run evals can be found in `docs/`.

## High level flow

This repo provides a small, end-to-end evaluation pipeline:

1. Dataset snapshot
	- Take a raw dataset (csv/jsonl) and build a versioned snapshot.
	- Output: `reports/datasets/<dataset_group_uid>/<dataset_version>/*.jsonl`

2. Prompt rendering
	- Render prompts from snapshot rows (and optional reference outputs).
	- Output: `reports/prompts_rendered/<dataset_group_uid>/<dataset_version>/*.jsonl`

3. Model output generation
	- Run generation adapters (LLM, mock, or task-specific adapters) to produce model outputs.
	- Output: `reports/model_outputs/<dataset_group_uid>/<dataset_version>/*.jsonl`

4. Evaluation (judging)
	- Run judges (rule-based for now) to produce per-sample rule outcomes.
	- Output: `reports/eval_results/<dataset_group_uid>/<dataset_version>/*.rule.jsonl`

5. Metrics aggregation
	- Aggregate per-sample results into summary metrics.
	- For binary-labeled datasets, optionally compute confusion matrix and ROC/PR curves.
	- Output: `reports/eval_results/<dataset_group_uid>/<dataset_version>/*.rule.metrics.json`
	- Note: curves/confusion-matrix require `binary_label_key` and `--include-curves`.

