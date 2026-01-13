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
     api/                                    # eval config files, json or yaml
      cli/
        build_dataset_snapshot_cli.py        # build local dataset snapshot jsonl + meta
        render_prompts_cli.py                # render prompt templates with local samples jsonl
        generate_model_outputs_cli.py        # run generation on rendered prompts and write model outputs jsonl
      datasets/
        adapters/                            # dataset-specific parsing and normalization
          truthfulqa.py
        dataset_loader.py                    # iterators for csv/jsonl loading
        dataset_types.py                     # TypedDict records for dataset rows and snapshot meta
      prompts/
        prompt_template.py                   # parse prompt path, load template, render placeholders
        prompt_types.py                      # RenderedPrompt TypedDict
      generation/
        generation_types.py                  # GenerationRequest/Response, Usage, ModelOutput
        generation_runner.py                 # run_one_generation/run_generation helpers
        adapters/
          __init__.py                        # register adapters
          base.py                            # adapter Protocol + registry
          mock_adapter.py                    # mock provider implementation
      services/                              # store-oriented services (Postgres/Redis), later phases
      utils/
        file_io.py                           # shared file helpers
        time_utils.py                        # utc_now_iso8601 helpers
      api/                                   # api for later phases
      workers/                               # async workers for later phases
      db.py                                  # SQLAlchemy engine/session helpers
    scripts/
      run_truthfulqa_snapshot.sh             # one-click: build TruthfulQA snapshot
      run_truthfulqa_rendered_prompts.sh     # one-click: render prompts v1/v2 for mini snapshot
      run_truthfulqa_model_outputs.sh        # one-click: generate model outputs from rendered prompts
    tests/
      test_build_dataset_snapshot_cli.py
      test_dataset_loader.py
      test_prompt_rendering.py
      test_render_prompts_cli.py
      test_generation_runner.py
      test_smoke.py
      test_smoke_db_seed.py
    alembic.ini
    pyproject.toml
    migrations/                              # alembic migrations (later phases)
  data/
    snapshots/                               # local dataset snapshot artifacts
      mini_truth.jsonl
      dataset_snapshot.json
  prompts/
    truthfulqa_generation_base/
      v1.txt
      v2.txt
  reports/
    rendered_prompts/
      truthfulqa_generation_base/
        v1.jsonl
        v2.jsonl
    model_outputs/
      truthfulqa_generation_base/
        v1.jsonl
  docs/
    dataset_loader.md
    prompt_rendering.md
    model_output_generation.md
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

Dataset ingestion and snapshot building

- `dataset_loader.py`: streaming readers for csv/jsonl.
- `adapters/`: dataset-specific logic. Example: `truthfulqa.py`.

**backend/app/prompts**

Prompt template rendering.

- `prompt_template.py`: defines prompt path conventions, reads `.txt`, and renders placeholders by simple replacement.

**backend/app/generation**

Model generation (separate from evaluation/judging).

- `generation_types.py`: JSONL schemas and request/response contracts (GenerationRequest, GenerationResponse, Usage, ModelOutput).
- `generation_runner.py`: helper functions that call an adapter and build ModelOutput rows.
- `adapters/: provider` adapters + a registry for lookup by provider.

**backend/app/services**
Store-oriented service layer (PostgreSQL/Redis). This is intentionally minimal early on.

**backend/app/utils**

Shared file utilities.

- `file_io.py`: helpers like `ensure_parent_dir`, `read_json`, `write_json`.
- `time_utils.py`: timestamp helpers.

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

