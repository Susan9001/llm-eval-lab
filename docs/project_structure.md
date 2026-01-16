# Project structure

Below is the important directory layout. Some folders are scaffolding for later phases, but are kept to avoid future refactors.

```text
llm-eval-lab/
  backend/
    app/
      api/                                   # API endpoints (scaffolding for later phases)
      cli/
        aggregate_metrics_cli.py             # aggregate metrics from eval results
        build_dataset_snapshot_cli.py        # build local dataset snapshot jsonl + meta
        generate_model_outputs_cli.py        # run generation on rendered prompts and write model outputs jsonl
        render_prompts_cli.py                # render prompt templates with local samples jsonl
        run_eval_cli.py                      # run evaluation: join rendered_prompts + model_outputs, run judges
      common/
        statuses.py                          # shared status constants
      configs/                               # config files (scaffolding for later phases)
      datasets/
        adapters/                            # dataset-specific parsing and normalization
          agnews_harmful.py                  # AG News with binary harmful labels adapter
          base.py                            # base adapter protocol and registry
          truthfulqa.py                      # TruthfulQA adapter
        dataset_loader.py                    # iterators for csv/jsonl loading
        dataset_types.py                     # TypedDict records for dataset rows and snapshot meta
      db.py                                  # SQLAlchemy engine/session helpers
      eval/
        aggregators/                         # metrics aggregation stage
          metrics/                           # summary metrics (confusion matrix, ROC/PR curves)
            aggregate_metrics.py             # build_metrics(...) entry point
            bucket_accumulator.py            # accumulate summary metrics + confusion-matrix counts
            curves_accumulator.py            # accumulate curve pairs and build ROC/PR curves + AUC
            metrics_types.py                 # TypedDict schemas for JSON output
          regression/                        # regression metrics (scaffolding for later phases)
        eval_runner.py                       # Evaluation runner, joins rendered_prompts and model_outputs, runs judges
        eval_types.py                        # TypedDict contracts for evaluation: EvalRequest, EvalResultRow, RuleOutcome
        judges/
          adapters/
            base.py                          # JudgeAdapter Protocol, adapter registry, build_judge_adapter entry point
            llm_adapter.py                   # LLM-as-judge adapter placeholder, kept for extensibility
            rule_adapter.py                  # rule-based judge adapter, runs a list of composable rules
          rules/
            base.py                          # Rule Protocol, rule registry, build_rules helper
            exact_match_reference.py         # rule: output_text exactly matches reference_output
            harmful_label_match.py           # rule: compares predicted binary label vs dataset label
            harmful_score.py                 # rule: reads score-like outcome (float) for metrics/curves demo
            non_empty_output.py              # rule: output_text is non-empty
      generation/
        adapters/
          base.py                            # adapter Protocol + registry
          harmful_score_adapter.py           # adapter that returns a score-like float for demo
          mock_adapter.py                    # mock provider implementation
        generation_runner.py                 # run_one_generation/run_generation helpers
        generation_types.py                  # GenerationRequest/Response, Usage, ModelOutputRow
      models/                                # SQLAlchemy ORM models (for later phases)
        schema.py                            # database schema definitions
      prompts/
        prompt_template.py                   # parse prompt path, load template, render placeholders
        prompt_types.py                      # RenderedPrompt TypedDict
      services/                              # store-oriented services (Postgres/Redis), later phases
        datasets_svc.py
        eval_results_svc.py
        eval_runs_svc.py
        model_outputs_svc.py
        prompts_svc.py
        samples_svc.py
      utils/
        file_io.py                           # shared file helpers
        time_utils.py                        # utc_now_iso8601 helpers
      workers/                               # async workers (scaffolding for later phases)
    migrations/                              # alembic migrations (later phases)
    scripts/
      run_agnews_harmful_aggregate_metrics.sh
      run_agnews_harmful_eval.sh
      run_agnews_harmful_model_outputs.sh
      run_agnews_harmful_rendered_prompts.sh
      run_agnews_harmful_snapshot.sh
      run_truthfulqa_aggregate_metrics.sh
      run_truthfulqa_eval.sh
      run_truthfulqa_model_outputs.sh
      run_truthfulqa_rendered_prompts.sh
      run_truthfulqa_snapshot.sh
    tests/
    alembic.ini
    pyproject.toml
  data/
    snapshots/                               # local dataset snapshot artifacts
      mini_truth.jsonl
      dataset_snapshot.json
  docs/
    database_schema.md
    dataset_loader.md
    model_output_generation.md
    project_structure.md
    prompt_rendering.md
    rule_based_evaluation.md
    aggregate_metrics.md
  prompts/
    agnews_harmful/
      v1.txt
      v2.txt
    truthfulqa_generation_base/
      v1.txt
      v2.txt
  reports/
    eval_results/
      agnews_harmful/
        v1.rule.jsonl
      truthfulqa_generation_base/
        v1.rule.jsonl
    metrics/
      agnews_harmful/
        v1.rule.metrics.json
      truthfulqa_generation_base/
        v1.rule.metrics.json
    model_outputs/
      agnews_harmful/
        v1.jsonl
      truthfulqa_generation_base/
        v1.jsonl
    rendered_prompts/
      agnews_harmful/
        v1.jsonl
        v2.jsonl
      truthfulqa_generation_base/
        v1.jsonl
        v2.jsonl
  docker-compose.yml
  Makefile
  README.md
```

## What each directory is for

**backend/app/cli**

Project entry points. These files parse arguments and orchestrate the local workflow.

**backend/app/datasets**

Dataset ingestion and snapshot building

- `dataset_loader.py`: streaming readers for csv/jsonl.
- `adapters/`: dataset-specific logic. Example: `truthfulqa.py` for [Truthful QA](https://github.com/sylinrl/TruthfulQA/tree/main?tab=readme-ov-file), and `agnews_harmful.py` for [ag_news](https://huggingface.co/datasets/fancyzhx/ag_news) with appended binary "Harmful" labels.

**backend/app/prompts**

Prompt template rendering.

- `prompt_template.py`: defines prompt path conventions, reads `.txt`, and renders placeholders by simple replacement.

**backend/app/generation**

Model generation (separate from evaluation/judging).

- `generation_types.py`: JSONL schemas and request/response contracts (GenerationRequest, GenerationResponse, Usage, ModelOutputRow).
- `generation_runner.py`: helper functions that call an adapter and build ModelOutputRow rows.
- `adapters/: provider` adapters + a registry for lookup by provider. Currently they are mocked 

**backend/app/eval**

Evaluation and judging pipeline (separate from generation). It joins `RenderedPrompt` and `ModelOutputRow`, runs a judge, and produces `EvalResultRow` artifacts.

- `eval_runner.py`: orchestrates judge execution for a dataset split.
- `eval_types.py`: shared eval datatypes (EvalResultRow, RuleOutcome, etc.).
- `judges/`: pluggable judge implementations.
  - `adapters/`: judge adapter registry and concrete adapters. `RuleAdapter` is implemented, `LLMAdapter` is a placeholder for extensibility.
  - `rules/`: composable rule units and a rule registry, such as `non_empty_output`, `exact_match_reference`. It also includes rules for binary supervised tasks (sepecific to harmfulness tasks as demo):
    - `harmful_label_match.py`: compares predicted binary label vs dataset label.
    - `harmful_score.py`: reads score-like outcome (float) for metrics/curves demo.
- `metrics/`: Metrics aggregation stage. Reads per-sample eval outputs (e.g. `*.rule.jsonl`) and produces summary metrics (e.g. `*.rule.metrics.json`).
  - `aggregate_metrics.py`: `build_metrics(...)` entry. Handles bucketing (overall / by_model_name / by_prompt_version).
  - `bucket_accumulator.py`: accumulates summary metrics + confusion-matrix counts for a bucket.
  - `curves_accumulator.py`: accumulates curve pairs and builds ROC/PR curves + AUC (optional).
  - `metrics_types.py`: TypedDict schemas for JSON output (`MetricsJson`, `BucketBundle`, `CurvesBundle`, etc.).


**backend/app/services**
Store-oriented service layer (PostgreSQL/Redis). This is intentionally minimal early on.

**backend/app/utils**

Shared file utilities.

- `file_io.py`: helpers like `ensure_parent_dir`, `read_json`, `write_json`.
- `time_utils.py`: timestamp helpers.

**backend/scripts**

Example scripts to run common workflows without remembering long commands.

AGNews harmful (binary label + curves):
- `run_agnews_harmful_snapshot.sh`
- `run_agnews_harmful_rendered_prompts.sh`
- `run_agnews_harmful_model_outputs.sh`
- `run_agnews_harmful_eval.sh`
- `run_agnews_harmful_aggregate_metrics.sh`

TruthfulQA (non-binary demo):
- `run_truthfulqa_snapshot.sh`
- `run_truthfulqa_rendered_prompts.sh`
- `run_truthfulqa_model_outputs.sh`
- `run_truthfulqa_eval.sh`
- `run_truthfulqa_aggregate_metrics.sh`

**data/**

Local data artifacts produced by snapshot builders, used as stable inputs for prompt rendering.

**prompts/**

Human-authored prompt templates. Versioning is done by filename, such as `v1.txt`, `v2.txt`.

**reports/**

Generated outputs, primarily rendered prompts and later evaluation reports.

**docs/**

Project docs and design notes.