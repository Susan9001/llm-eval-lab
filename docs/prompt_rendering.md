# Prompt Rendering

This codepath renders prompt template with samples.

## Where Things Live

Recommended layout:

1. `backend/app/prompts/prompt_template.py`  
   Prompt path conventions, reading `.txt` templates, and rendering placeholders.
2. `backend/app/cli/render_prompts_cli.py`  
   CLI entrypoint that renders one or more prompt templates against a local samples snapshot JSONL.
3. `prompts/`  
   Human-authored prompt templates, versioned by filename (e.g. `v1.txt`, `v2.txt`).
4. `data/snapshots/`  
   Local samples snapshot JSONL (e.g. `mini_truth.jsonl`).
5. `reports/rendered_prompts/`  
   Rendered prompt artifacts (JSONL), organized by `{prompt_group_uid}/{prompt_version}.jsonl`.

## Inputs

### Prompt templates

Location: `prompts/`

Example:

- `prompts/truthfulqa_generation_base/v1.txt`
- `prompts/truthfulqa_generation_base/v2.txt`

Naming convention:

- Version is derived from filename stem, such as `v1` from `v1.txt`.
- `prompt_group_uid` is derived from the relative path under `prompts/`, joining all parent directories with `_`.

Example:

- `truthfulqa_generation_base/v1.txt`
  - `prompt_group_uid`: `truthfulqa_generation_base`
  - `prompt_version`: `v1`

Supported placeholders:

- `{input_text}`: required for generation prompts.
- `{reference_output}`: optional, only if your sample jsonl contains it.
- `{output_text}`: optional, intended for judge prompts later.

Rendering strategy:

- Simple string replacement with `str.replace`.
- If a template contains `{reference_output}` but the sample row does not provide `reference_output`, rendering fails fast with a `ValueError`.
- If a template contains `{output_text}` but `output_text` is missing, rendering fails fast with a `ValueError`.

Code: `backend/app/prompts/prompt_template.py`.

### Samples snapshot jsonl

Location: `data/snapshots/`

Example: `data/snapshots/mini_truth.jsonl`

Each line is a JSON object. Minimum required fields:

- `source_sample_id`: string
- `input_text`: string

Optional fields:

- `reference_output`: string or null
- `metadata`: JSON object or null

## Outputs

Location: `reports/rendered_prompts/`

For each prompt template, one output jsonl is produced:

- `reports/rendered_prompts/{prompt_group_uid}/{prompt_version}.jsonl`

Each line contains:

- `prompt_group_uid`
- `prompt_version`
- `prompt_path` (relative path under prompts root)
- `source_sample_id`
- `input_text`
- `rendered_prompt`
- `reference_output` (only if present)

## How to run

### Option A: One-click script

```bash
bash backend/scripts/run_truthfulqa_rendered_prompts.sh
```

This renders the default prompt set:

- `truthfulqa_generation_base/v1.txt`
- `truthfulqa_generation_base/v2.txt`

using:

- `data/snapshots/mini_truth.jsonl`

and writes outputs to:

- `reports/rendered_prompts/`

### Option B: Run the CLI directly

From repo root:

```bash
PYTHONPATH=backend python backend/app/cli/render_prompts_cli.py \
  truthfulqa_generation_base/v1.txt truthfulqa_generation_base/v2.txt \
  --prompts-root prompts \
  --samples-jsonl-path data/snapshots/mini_truth.jsonl \
  --rendered-prompts-dir reports/rendered_prompts
```

### Tests

Relevant tests:

- `backend/tests/test_prompt_rendering.py`
  - tests `parse_prompt_path`
  - tests `render_prompt`
- `backend/tests/test_render_prompts_cli.py`
  - tests `render_and_write_one_prompt`
  - tests end-to-end `render_prompts`

Run all tests:

```bash
make test
```

## Future work

Later phases can extend the pipeline to:

- store prompt templates and rendered prompts in DB
- create `PENDING` model outputs and run a model API
- add judge prompts and aggregate eval results
