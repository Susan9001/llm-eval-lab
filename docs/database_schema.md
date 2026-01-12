# Database schema

The goal of the DB scheme is to:

1. Make runs reproducible and comparable.
2. Support both workflows:
   - Generate then evaluate.
   - Evaluate only (import existing outputs).
3. Allow multiple evaluations on the same output, for example different metrics, judges, or versions.

## Glossary

- **Dataset**: a versioned evaluation dataset row in `datasets` identified by name plus version plus optional split.
- **Sample**: one canonicalized input row from a dataset.
- **Model output**: a concrete output produced or imported for a sample under some generation setting.
- **Evaluation**: a scoring or judging step applied to a model output.
- **Run**: a single evaluation job configuration applied to one dataset.

## Tables

### datasets

Versioned evaluation datasets.

Key fields:

- `dataset_id`: internal primary key.
- `dataset_group_uid `: dataset name, for example `truthfulqa` or `realtotoxicityprompts`.
- `display_name`: optional human readable name, safe to rename without breaking grouping.
- `version`: dataset version string, for example `v1` or `2026_01_09`.
- `split`: optional, for example `train`, `test`, `validation`, `prod_logs`.
- `description`: human readable description.
- `source`: where the data came from, for example HuggingFace, logs, manual curation.
- `sampling_spec` JSONB: sampling and filtering rules, including seed, filters, ratios.
- `content_hash`: optional fingerprint of the canonicalized snapshot, used for reproducibility.
- `num_samples`: optional sample count.
- `status`: `BUILDING`, `READY`, or `DEPRECATED`.
- `created_at`: timestamp.

Uniqueness:

- `UNIQUE(dataset_group_uid, version, split)` keeps each dataset version distinct.

### samples

Canonicalized inputs for evaluation, belonging to a specific dataset row.

Key fields:

- `sample_id`: primary key.
- `dataset_id`: foreign key to `datasets.dataset_id`.
- `source_sample_id`: original row identifier from source dataset or logs, if available.
- `input_text`: the input content that will be bound into prompts, often the user query or question.
- `reference_output`: optional reference answer or label, used by some metrics.
- `metadata` JSONB: optional tags, such as category, topic, difficulty, jailbreak type.
- `created_at`: timestamp.

Uniqueness:

- `UNIQUE(dataset_id, source_sample_id)` prevents duplicate imports from the same source.

Typical index:

- `samples(dataset_id)` for joining samples under a dataset.

### prompts

Prompt templates with built in versioning.

Each row is a concrete version of a prompt. `prompt_group_uid` groups versions that belong to the same logical prompt family.

Key fields:

- `prompt_id`: primary key.
- `prompt_group_uid`: human-readable stable identifier for a prompt family.
   - Use lowercase snake_case only, with characters limited to [a-z0-9_].
   - Must start with a letter, must not contain spaces or special characters, and should be treated as immutable once created.
   - Examples: truthfulqa_generation_base, truthfulness_judge_binary.
- `purpose`: `GENERATION` or `JUDGE`.
- `version`: version string within the group, for example `v1`, `v2`, or a date.
- `display_name`: optional human readable name, safe to rename without breaking grouping.
- `description`: optional long-form description for the prompt.
- `template_text`: full prompt template text, which may contain placeholders such as `{input_text}` or `{output_text}`.
- `metadata` JSONB: optional extra information, for example variable descriptions or output format notes.
- `created_at`: timestamp.

Uniqueness:

- `UNIQUE(prompt_group_uid, version)` ensures one row per version within a group.

Prompts are referenced from:

- `model_outputs.generation_prompt_id` when the system itself generates outputs.
- `eval_runs.judge_prompt_id` when a judge model uses a prompt to score outputs.

### model_outputs

Generated or imported outputs for a sample.

Key fields:

- `output_id`: primary key.
- `sample_id`: foreign key to `samples.sample_id`.
- `generation_prompt_id`: optional foreign key to `prompts.prompt_id`, pointing to a `purpose = 'GENERATION'` prompt when the system itself generated the output.
- `provider`: optional source, for example `openai`, `anthropic`, or `local`.
- `model_name`: optional model identifier, for example `gpt-4.1`.
- `generation_params` JSONB: optional parameters such as `temperature`, `top_p`, or `max_tokens`.
- `generation_status`: `PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`, or `SKIPPED` for the generation or import step.
- `output_text`: the output content when it is small enough to store inline.
- `output_artifact_uri`: pointer to a large artifact, for example a JSON file in object storage, when outputs or traces are large.
- `generation_error_message`: error message for generation or import failures only.
- `created_at`, `started_at`, `finished_at`: timestamps.

Why a separate table:

- One `sample` can have many `model_outputs` for different models, parameters, retries, or imported outputs.
- The same `model_outputs` row can be evaluated many times by different runs.

Typical indexes:

- `model_outputs(sample_id)`.
- `model_outputs(generation_status)`.

### eval_runs

An evaluation run is a job configuration applied to exactly one dataset row name plus version plus split.

Key fields:

- `run_id`: internal primary key.
- `run_uid`: external identifier for command line, logs, and URLs, recommended to be a UUID.
- `dataset_id`: foreign key to `datasets.dataset_id`, the dataset being evaluated.
- `judge_prompt_id`: foreign key to `prompts.prompt_id`, pointing to a `purpose = 'JUDGE'` prompt if a judge prompt is used.
- `eval_name`: name of the evaluator, for example `llm_judge`, `rule_based`, or `toxicity_classifier`.
- `eval_params` JSONB: evaluator configuration, for example judge model name, thresholds, output parsing flags, few shot retrieval settings.
- `run_status`: `PENDING`, `RUNNING`, `SUCCEEDED`, or `FAILED` at the run level.
- `git_commit`: optional code version hash for traceability.
- `config_name`: optional human readable configuration name.
- `parent_run_id`: optional foreign key to another `eval_runs.run_id`, used to group multiple child runs into a suite.
- `created_at`, `started_at`, `finished_at`: timestamps.

Design notes:

- One `eval_run` evaluates exactly one dataset row. This keeps aggregation and comparisons straightforward.
- For a multi dataset benchmark, use a parent run with `parent_run_id` on each child run. The parent may leave `dataset_id` null and act purely as a logical container.

### eval_results

Evaluation results for a given output under a given run.

Key fields:

- `result_id`: primary key.
- `run_id`: foreign key to `eval_runs.run_id`.
- `output_id`: foreign key to `model_outputs.output_id`.
- `eval_status`: `PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`, or `SKIPPED` for the evaluation step.
- `scores` JSONB: map of metric name to values, for example

  ```json
  {
    "truthfulness": 0.8,
    "toxicity": 0.1,
    "overall": 0.75
  }
  ```

- `rationale`: optional explanation or summary reasoning from the judge or rule engine.
- `eval_error_message`: error message for evaluation failures only.
- `created_at`, `started_at`, `finished_at`: timestamps.

Uniqueness:

- `UNIQUE(run_id, output_id)` ensures that a given run evaluates a given output at most once.

Typical indexes:

- `eval_results(run_id)` for aggregations per run.
- `eval_results(output_id)` for looking up all evaluations of a given output.
- `eval_results(eval_status)` for scheduling and monitoring.

## Typical workflows

### Generate then evaluate

1. Insert a `datasets` row with `name`, `version`, `split`, and `sampling_spec`.
2. Insert `samples` for that dataset.
3. For each sample, create a `model_outputs` row with `generation_status = 'PENDING'`.
4. A generator worker:
   - Reads pending rows.
   - Calls the model using the appropriate generation prompt.
   - Fills `output_text` or `output_artifact_uri`.
   - Sets `generation_status` and timestamps, and fills `generation_error_message` on failure.
5. Create an `eval_run` for this dataset and evaluator configuration.
6. For each `model_outputs` row, create an `eval_results` row with `eval_status = 'PENDING'`.
7. An evaluator worker:
   - Reads pending evaluation rows.
   - Applies the evaluator or judge prompt.
   - Fills `score` and `rationale`.
   - Updates `eval_status` and timestamps, and fills `eval_error_message` on failure.

### Evaluate only, import existing outputs

1. Insert a `datasets` row and `samples`, for example canonicalized from logs.
2. Insert `model_outputs` rows with `generation_status = 'SUCCEEDED` and `output_text` or `output_artifact_uri` filled.
3. Create an `eval_run` for this dataset and evaluator configuration.
4. Insert `eval_results` rows, one per `output_id`, with `eval_status = 'PENDING'`.
5. Run the evaluator worker as above.

This workflow is used for offline evaluation of production logs or pre generated outputs.

### Multiple evaluations on the same output

- Reuse the same `model_outputs.output_id`.
- Create multiple `eval_runs` with different `eval_name`, `eval_params`, or judge prompts.
- Each run produces its own `eval_results` rows for that `output_id`.

This supports:

- Comparing different judges or metrics.
- Comparing different scoring thresholds or settings.
- Progressive refinement of evaluation logic on the same underlying outputs.
