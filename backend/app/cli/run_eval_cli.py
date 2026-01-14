from __future__ import annotations

import argparse
from dataclasses import dataclass

import jsonlines

from app.eval.eval_runner import iter_eval_results
from app.utils.file_io import ensure_parent_dir, iter_rows_from_jsonl

rendered_prompt_required_keys = [
  "dataset_group_uid",
  "dataset_version",
  "split",
  "source_sample_id",
  "prompt_group_uid",
  "prompt_version",
]
model_output_required_keys = [
  "dataset_group_uid",
  "dataset_version",
  "split",
  "source_sample_id",
  "prompt_group_uid",
  "prompt_version",
  "model_output_uuid",
  "provider",
  "model_name",
  "generation_status",
]


@dataclass(frozen=True)
class EvalCliArgs:
  model_outputs_path: str
  rendered_prompts_path: str
  eval_results_path: str
  rule_names: list[str]
  judge_type: str
  judge_model_name: str | None


def _parse_rule_names(value: str) -> list[str]:
  names = [x.strip() for x in value.split(",")]
  names = [x for x in names if x]
  if not names:
    raise argparse.ArgumentTypeError(
      "--rule-names must contain at least one rule name."
    )
  return names


def parse_args() -> EvalCliArgs:
  parser = argparse.ArgumentParser(
    description="Run evaluation (rule-based for now) and write eval_results.jsonl.",
  )

  parser.add_argument(
    "--model-outputs-path",
    required=True,
    help="Path to model_outputs.jsonl.",
  )
  parser.add_argument(
    "--rendered-prompts-path",
    required=True,
    help="Path to rendered_prompts.jsonl.",
  )
  parser.add_argument(
    "--eval-results-path",
    required=True,
    help="Output path for eval_results.jsonl.",
  )
  parser.add_argument(
    "--rule-names",
    required=True,
    type=_parse_rule_names,
    help="Comma-separated rule names, e.g. non_empty_output,exact_match_reference",
  )

  # Optional placeholders.
  parser.add_argument(
    "--judge-type",
    default="rule",
    help="Judge type. For now only 'rule' is supported.",
  )
  parser.add_argument(
    "--judge-model-name",
    default=None,
    help="Placeholder for LLM-as-judge. Not used today.",
  )

  ns = parser.parse_args()

  if ns.judge_type != "rule":
    raise ValueError("Only --judge-type=rule is supported today.")

  return EvalCliArgs(
    model_outputs_path=ns.model_outputs_path,
    rendered_prompts_path=ns.rendered_prompts_path,
    eval_results_path=ns.eval_results_path,
    rule_names=ns.rule_names,
    judge_type=ns.judge_type,
    judge_model_name=ns.judge_model_name,
  )


def run_evals(args: EvalCliArgs) -> None:
  rendered_prompts = iter_rows_from_jsonl(
    args.rendered_prompts_path,
    required_keys=rendered_prompt_required_keys,
  )

  model_output_rows = iter_rows_from_jsonl(
    args.model_outputs_path,
    required_keys=model_output_required_keys,
  )

  ensure_parent_dir(args.eval_results_path)

  judge_name = "rule_judge"
  judge_version = None

  judge_adapter_kwargs: dict[str, object] = {
    "rule_names": args.rule_names,
  }

  num_written = 0
  with jsonlines.open(args.eval_results_path, mode="w") as writer:
    for row in iter_eval_results(
      rendered_prompts=rendered_prompts,
      model_output_rows=model_output_rows,
      judge_type=args.judge_type,
      judge_name=judge_name,
      judge_version=judge_version,
      judge_adapter_kwargs=judge_adapter_kwargs,
    ):
      writer.write(row)
      num_written += 1

  print(f"Wrote {num_written} rows to {args.eval_results_path}")


if __name__ == "__main__":
  run_evals(parse_args())
