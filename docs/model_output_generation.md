# Model Output Generation

This codepath turns rendered prompts into model outputs by calling a generation provider (mock provider supported today). The output is a JSONL file where each line is one `ModelOutputRow`.

## Where Things Live

Recommended layout:

1. `backend/app/generation/generation_types.py`  
   Core TypedDict schemas (`GenerationRequest`, `GenerationResponse`, `Usage`, `ModelOutputRow`).
2. `backend/app/generation/generation_runner.py`  
   Small orchestration helpers (`run_one_generation`, `run_generation`, and optional iterators).
3. `backend/app/generation/adapters/`  
   Provider adapters, plus a registry for lookup by `provider`.
   - `base.py`: adapter Protocol + registry helpers.
   - `mock_adapter.py`: mock implementation used for tests and local runs.
4. `backend/app/cli/generate_model_outputs_cli.py`  
   CLI entrypoint that reads rendered prompts JSONL and writes model outputs JSONL.
5. `backend/scripts/run_truthfulqa_model_outputs.sh`  
   One-click script that wires together default TruthfulQA paths.

## Input

### Rendered prompts JSONL

Location: `reports/rendered_prompts/`

Example:

- `reports/rendered_prompts/truthfulqa_generation_base/v1.jsonl`

Each line is a JSON object. Minimum required fields:

- `dataset_group_uid`
- `dataset_version`
- `split`
- `prompt_group_uid`
- `prompt_version`
- `source_sample_id`
- `rendered_prompt`

Optional fields:

- `prompt_path`
- `input_text`
- `reference_output`

## Output

Location: `reports/model_outputs/`

Example:

- `reports/model_outputs/truthfulqa_generation_base/v1.jsonl`

Each line is a `ModelOutputRow` JSON object. Minimum required fields:

- `model_output_uuid`
- `dataset_group_uid`
- `dataset_version`
- `split`
- `source_sample_id`
- `prompt_group_uid`
- `prompt_version`
- `prompt_path` (can be null)
- `provider`
- `model_name`
- `generation_params` (can be `{}` or null if you allow it)
- `output_text`
- `generation_status`
- `generation_error_message`
- `usage_json`
- `started_at`
- `finished_at`
- `latency_ms`

Notes:

- `started_at` and `finished_at` are ISO-8601 UTC strings (second resolution) from `utc_now_iso8601()`.
- `latency_ms` is measured using `time.perf_counter()` (millisecond integer), so it does not depend on parsing timestamp strings.

## Core Data Structures (optional)

### GenerationRequest

Fields:

- `rendered_prompt`: string
- `provider`: string
- `model_name`: string
- `generation_params`: dict (recommend `{}` as default)

### GenerationResponse

Adapter return contract:

- `output_text`: string or null
- `generation_status`: string
- `generation_error_message`: string or null
- `usage_json`: `Usage`

### Usage

Mock-friendly usage schema. In mock runs, you can fill only what is meaningful and keep the rest as null.

Suggested fields:

- `prompt_tokens`: int or null
- `completion_tokens`: int or null
- `total_tokens`: int or null
- `provider_request_id`: string or null
- `finish_reason`: string or null
- `cost_usd`: float or null

### ModelOutputRow

A self-describing output row that combines dataset identity, prompt identity, provider info, and the generation result.

## How to run

### Option A: One-click script

```bash
bash backend/scripts/run_truthfulqa_model_outputs.sh
```

This script:

- reads rendered prompts from `reports/rendered_prompts/truthfulqa_generation_base/`
- writes model outputs to `reports/model_outputs/truthfulqa_generation_base/`

Defaults are intended for local smoke runs (e.g. `provider=mock`).

### Option B: Run the CLI directly

```bash
PYTHONPATH=backend python backend/app/cli/generate_model_outputs_cli.py \
  --rendered-prompts-jsonl-path reports/rendered_prompts/truthfulqa_generation_base/v1.jsonl \
  --out-jsonl-path reports/model_outputs/truthfulqa_generation_base/v1.jsonl \
  --provider mock \
  --model-name mock-model \
  --generation-params-json '{"temperature":0.0,"max_tokens":64}'
```

### Run tests:

```bash
pytest backend/tests/test_generation_runner.py -q
```


## Artifacts (optional)

- Model outputs JSONL: `reports/model_outputs/{prompt_group_uid}/{prompt_version}.jsonl`
- The file is self-describing (it carries dataset and prompt identity fields), so it can be replayed without DB IDs.

## Design notes

- Generation outputs are intentionally separate from evaluation outputs (judge results). `ModelOutputRow` captures what the model produced; evaluation results belong in `eval_results`.
- Caching is intentionally not part of the minimal local pipeline. It can be added later when DB persistence and repeated runs make cache value obvious.
