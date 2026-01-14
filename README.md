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

CLIs to generate model outputs and run eval can be found in `docs/`.

## High level flow

1. `build_dataset_snapshot_cli.py` writes `data/snapshots/*.jsonl`.
2. `render_prompts_cli.py` reads snapshots and prompt templates, writes `reports/rendered_prompts/*.jsonl`.
3. `generate_model_outputs_cli.py` reads rendered prompts, calls a generation adapter, writes `reports/model_outputs/*.jsonl`.
4. `run_eval_cli.py` joins rendered prompts and model outputs, applies a judge adapter, writes `reports/eval_results/*.jsonl`.

