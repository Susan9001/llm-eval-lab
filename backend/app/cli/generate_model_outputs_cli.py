from typing import Any

import app.generation.adapters  # noqa: F401  (trigger registration)
from dataclasses import dataclass
import argparse
from app.utils.file_io import read_json, ensure_parent_dir, iter_rows_from_jsonl
from app.prompts.prompt_types import RenderedPrompt
from app.generation.generation_runner import iter_generation_outputs
import jsonlines
from app.generation.generation_types import ModelOutput
import json

requred_prompt_keys = [
  "prompt_group_uid",
  "prompt_version",
  "source_sample_id",
  "rendered_prompt",
]


@dataclass(frozen=True)
class GenerateModelOutputsCliArgs:
  """CLI args for local model output generation (day5)."""

  rendered_prompts_jsonl_path: str
  out_jsonl_path: str

  provider: str  # e.g. "mock"
  model_name: str  # e.g. "mock-model"
  generation_params: dict[str, Any]  # normalized to {} if not provided


def parse_args() -> GenerateModelOutputsCliArgs:
  parser = argparse.ArgumentParser(
    description="Generate model outputs jsonl from rendered prompts jsonl."
  )
  parser.add_argument("--rendered-prompts-jsonl-path", required=True)
  parser.add_argument("--out-jsonl-path", required=True)

  parser.add_argument("--provider", default="mock")
  parser.add_argument("--model-name", default="mock-model")

  parser.add_argument("--generation-params-path", default=None)
  parser.add_argument("--generation-params-json", default=None)

  ns = parser.parse_args()

  in_path = ns.rendered_prompts_jsonl_path.strip()
  out_path = ns.out_jsonl_path.strip()
  if not in_path.endswith(".jsonl"):
    raise ValueError("rendered_prompts_jsonl_path must be a .jsonl file.")
  if not out_path.endswith(".jsonl"):
    raise ValueError("out_jsonl_path must be a .jsonl file.")

  provider = ns.provider.strip().lower()
  if not provider:
    raise ValueError("provider is empty.")
  model_name = ns.model_name.strip()
  if not model_name:
    raise ValueError("model_name is empty.")

  if ns.generation_params_path and ns.generation_params_json:
    raise ValueError(
      "Provide only one of --generation-params-path or --generation-params-json."
    )

  params: dict[str, Any] = {}
  if ns.generation_params_path:
    params = read_json(ns.generation_params_path)
    if not isinstance(params, dict):
      raise ValueError("--generation-params-path must point to a JSON object.")
  elif ns.generation_params_json:
    params = json.loads(ns.generation_params_json)
    if not isinstance(params, dict):
      raise ValueError("--generation-params-json must be a JSON object.")

  return GenerateModelOutputsCliArgs(
    rendered_prompts_jsonl_path=in_path,
    out_jsonl_path=out_path,
    provider=provider,
    model_name=model_name,
    generation_params=params,
  )


def load_rendered_prompts(
  rendered_prompts_jsonl_path: str,
) -> list[dict[str, Any]]:
  """Load rendered prompts from a local jsonl file."""
  prompts: list[RenderedPrompt] = []
  for row in iter_rows_from_jsonl(
    rendered_prompts_jsonl_path, required_keys=requred_prompt_keys
  ):
    prompts.append(row)
  return prompts


def write_model_outputs_jsonl(
  model_outputs: list[ModelOutput],
  out_jsonl_path: str,
) -> None:
  """Write model outputs to a local jsonl file."""
  ensure_parent_dir(out_jsonl_path)
  with jsonlines.open(out_jsonl_path, mode="w") as writer:
    for output in model_outputs:
      writer.write(output)


def generate_model_outputs(
  args: GenerateModelOutputsCliArgs,
) -> None:
  """Main process entry point:
  - Load rendered prompts from local jsonl.
  - Run model generation.
  - Write model outputs to local jsonl.
  """
  rendered_prompts = load_rendered_prompts(args.rendered_prompts_jsonl_path)

  ensure_parent_dir(args.out_jsonl_path)
  with jsonlines.open(args.out_jsonl_path, mode="w") as writer:
    for model_output in iter_generation_outputs(
      rendered_prompts,
      provider=args.provider,
      model_name=args.model_name,
      generation_params=args.generation_params,
    ):
      writer.write(model_output)


if __name__ == "__main__":
  args = parse_args()
  generate_model_outputs(args)
