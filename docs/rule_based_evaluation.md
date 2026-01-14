# Rule-based evaluation (judging)

This stage consumes `rendered_prompts.jsonl` and `model_outputs.jsonl`, joins them by a stable key, applies a rule-based judge, and writes one `EvalResultRow` per model output into `eval_results.jsonl`.

## Where things live

### Core logic

- `backend/app/eval/eval_runner.py`: joins inputs, builds `EvalRequest`, runs the judge adapter, and adds timestamps and latency.
- `backend/app/eval/eval_types.py`: `EvalRequest`, `EvalResultRow`, `RuleOutcome`, and status constants.

### Rule-based judge

- `backend/app/eval/judges/adapters/rule_adapter.py`: applies a list of rules and produces `EvalResultRow`.
- `backend/app/eval/judges/rules/base.py`: `Rule` Protocol, rule registry, and `build_rules()`.
- `backend/app/eval/judges/rules/non_empty_output.py`: example rule.
- `backend/app/eval/judges/rules/exact_match_reference.py`: example rule.

### Entry points

- `backend/app/cli/run_eval_cli.py`: CLI wrapper for running evaluation.
- `backend/scripts/run_truthfulqa_eval.sh`: one-click example script.

## Input

### Rendered prompts

A JSONL file produced by prompt rendering, typically under `reports/rendered_prompts/**/v1.jsonl`.

Each row is a `RenderedPrompt` and must contain the identity fields that make it joinable:

- Dataset snapshot identifier: `dataset_group_uid`, `dataset_version`, `split`
- Prompt identifier: `prompt_group_uid`, `prompt_version`
- Sample identifier: `source_sample_id`

It also contains content fields used by evaluation:

- `input_text` (optional, depends on task)
- `rendered_prompt`
- `reference_output` (optional, but needed for rules like exact match)

### Model outputs

A JSONL file produced by model output generation, typically under `reports/model_outputs/**/v1.jsonl`.

Each row is a `ModelOutputRow` and must include:

- `model_output_uuid` (unique output identity)
- `provider`, `model_name`
- `generation_status`, `generation_error_message` (if any)
- `output_text` (may be `None` if generation failed)

To make joining work, the model output row also carries the same rendered prompt identity fields listed above.

## Join key contract

Evaluation joins a model output row to a rendered prompt row by a stable key derived from:

- `dataset_group_uid`
- `dataset_version`
- `split`
- `prompt_group_uid`
- `prompt_version`
- `source_sample_id`

This key is effectively `RenderedPromptIdentifier` without `prompt_path`. The intent is that artifacts are self-describing and do not depend on database IDs.

## Output

### eval_results.jsonl

A JSONL file where each line is one `EvalResultRow`.

At a high level, each row contains:

- Identity: rendered prompt identity fields plus `model_output_uuid`, `provider`, `model_name`
- Judge metadata: `judge_type`, `judge_name`, `judge_version` (optional)
- Status: `eval_status`, `eval_error_message`
- Rule details: `rule_outcomes` as a mapping `{rule_name: RuleOutcome}`
- Timing: `started_at`, `finished_at`, `latency_ms`

`RuleOutcome` is intentionally small and composable:

- `status` (string)
- `score` (`float` or `None`)
- `rationale` (`str` or `None`)
- `error_message` (`str` or `None`)

## Core data structures

These names match the code:

- `RenderedPromptIdentifier` and `RenderedPrompt` live in `backend/app/prompts/prompt_types.py`
- `ModelOutputRow` lives in `backend/app/generation/generation_types.py`
- `EvalRequest`, `EvalResultRow`, `RuleOutcome` live in `backend/app/eval/eval_types.py`

`EvalRequest` is built by joining one rendered prompt row and one model output row.

## How to run

### Tests

From the repo root:

```bash
pytest -q backend/tests/test_eval_run.py
```

### Option A: one-click script

```bash
bash backend/scripts/run_truthfulqa_eval.sh
```

This script is expected to call the CLI with concrete file paths under `reports/`.

### Option B: run the CLI directly

Example:

```bash
PYTHONPATH=backend python backend/app/cli/run_eval_cli.py \
  --model-outputs-path reports/model_outputs/truthfulqa_generation_base/v1.jsonl \
  --rendered-prompts-path reports/rendered_prompts/truthfulqa_generation_base/v1.jsonl \
  --eval-results-path reports/eval_results/truthfulqa_generation_base/v1.jsonl \
  --rule-names non_empty_output,exact_match_reference \
  --judge-type rule \
  --judge-model-name placeholder
```

Notes:

- `--rule-names` is comma-separated.
- `--judge-type` can default to `rule`.
- `--judge-model-name` is a placeholder to keep the interface stable for future LLM-as-judge.

## Artifacts

- `reports/eval_results/**/v*.jsonl`: evaluation outputs. Each row is an `EvalResultRow`.

## Extensibility notes

- To add a new rule, implement the `Rule` Protocol and register it in `backend/app/eval/judges/rules/__init__.py`.
- To add LLM-as-judge later, implement a new judge adapter under `backend/app/eval/judges/adapters/` and register it in `backend/app/eval/judges/adapters/__init__.py`.
- Status fields are strings for now to keep iteration fast. Enums can be introduced once the surface area stabilizes.
