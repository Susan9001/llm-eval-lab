# llm-eval-lab

Evaluation lab for LLM quality and safety. Python + FastAPI + PostgreSQL + Redis, build for offline metrics, regression gating, and reporting.

## Tech stack

- Python (backend services)
- PostgreSQL (evaluation metadata and results)
- Redis (caching and task queue)
- Docker and Docker Compose (local orchestration)

## Project structure

Below is the important directory layout. Some folders are scaffolding for later phases, but are kept to avoid future refactors.

```text
llm-eval-lab/
  backend/
    app/
      cli/
        build_dataset_snapshot_cli.py        # build local dataset snapshot jsonl + meta
        render_prompts_cli.py                # render prompt templates with local samples jsonl
      datasets/
        adapters/                            # dataset-specific parsing and normalization
          truthfulqa.py
        dataset_loader.py                    # iterators for csv/jsonl loading
        dataset_types.py                     # TypedDict records for dataset rows
      prompts/
        prompt_template.py                   # parse prompt path, load template, render placeholders
      services/                              # DB oriented services, mostly for later phases
        datasets_service.py
        samples_service.py
        prompts_service.py
        model_outputs_service.py
        eval_runs_service.py
        eval_results_service.py
      utils/
        file_io.py                           # shared file helpers, e.g. ensure_parent_dir, read/write json
      db.py                                  # SQLAlchemy engine/session helpers (later phases)
    scripts/
      run_truthfulqa_snapshot.sh             # one-click: build TruthfulQA snapshot
      run_truthfulqa_rendered_prompts.sh     # one-click: render prompts v1/v2 for mini snapshot
    tests/
      test_build_dataset_snapshot_cli.py
      test_dataset_loader.py
      test_prompt_rendering.py
      test_render_prompts_cli.py
      test_smoke.py
      test_smoke_db_seed.py
    alembic.ini
    pyproject.toml
    migrations/                              # alembic migrations (later phases)
  data/
    snapshots/                               # local dataset snapshot artifacts
      mini_truth.jsonl                       # example mini snapshot
  prompts/
    truthfulqa_generation_base/
      v1.txt
      v2.txt
  reports/
    rendered_prompts/
      truthfulqa_generation_base/
        v1.jsonl
        v2.jsonl
  docs/
  docker-compose.yml
  Makefile
  README.md
```

### What each directory is for

**backend/app/cli**

Project entry points. These files parse arguments and orchestrate the local workflow.

- `build_dataset_snapshot_cli.py`: builds `data/snapshots/*.jsonl` from raw datasets.
- `render_prompts_cli.py`: renders `prompts/**/*.txt` with `data/snapshots/*.jsonl` and writes `reports/rendered_prompts/**/*.jsonl`.

**backend/app/datasets**

Dataset ingestion and snapshot building.

- `dataset_loader.py`: streaming readers for csv/jsonl.
- `adapters/`: dataset-specific logic. Example: `truthfulqa.py`.

**backend/app/prompts**

Prompt utilities.

- `prompt_template.py`: defines prompt path conventions, reads `.txt`, and renders placeholders by simple replacement.

**backend/app/utils**

Shared file utilities.

- `file_io.py`: helpers like `ensure_parent_dir`, `read_json`, `write_json`.

**backend/scripts**

Example scripts to run common workflows without remembering long commands.

**data/**

Local data artifacts produced by snapshot builders, used as stable inputs for prompt rendering.

**prompts/**

Human-authored prompt templates. Versioning is done by filename, such as `v1.txt`, `v2.txt`.

**reports/**

Generated outputs, primarily rendered prompts and later evaluation reports.

**docs/**

Project docs and design notes.

## Dependencies

```bash
pip install sqlalchemy psycopg2-binary python-dotenv pytest ruff jsonlines
```

## Quickstart

### Run tests

From repo root:

```bash
make pytest
```

