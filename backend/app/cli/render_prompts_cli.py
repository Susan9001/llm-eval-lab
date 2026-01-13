from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import jsonlines

from app.utils.file_io import iter_rows_from_jsonl
from app.datasets.dataset_types import (
  SampleRecord,
  DatasetSnapshotMeta,
  DatasetSnapshotIdentifier,
  extract_dataset_snapshot_identifier,
)
from app.prompts.prompt_types import RenderedPrompt
from app.prompts.prompt_template import (
  parse_prompt_path,
  load_prompt_text,
  render_prompt,
)
from app.utils.file_io import ensure_parent_dir, read_json

required_sample_keys = ["source_sample_id", "input_text"]


@dataclass(frozen=True)
class RenderPromptsCliArgs:
  """CLI args for local prompt rendering."""

  prompts_root: str
  prompt_paths: list[str]
  samples_jsonl_path: str
  snapshot_meta_path: str  # e.g. data/snapshots/dataset_snapshot.json
  rendered_prompts_dir: str


def parse_args() -> RenderPromptsCliArgs:
  import argparse

  parser = argparse.ArgumentParser(
    description="Render local prompt templates (.txt) using local samples (.jsonl), then write rendered prompts as jsonl."
  )

  parser.add_argument(
    "prompt_paths",
    nargs="+",
    help='Prompt path(s) relative to prompts root, e.g. "truthfulqa_generation_base/v1.txt" "truthfulqa_generation_base/v2.txt".',
  )
  parser.add_argument(
    "--prompts-root",
    type=str,
    default="prompts",
    help="Root directory that contains prompt files. Default: prompts",
  )
  parser.add_argument(
    "--samples-jsonl-path",
    type=str,
    required=True,
    help="Local jsonl snapshot of samples, e.g. data/snapshots/mini_truth.jsonl",
  )
  parser.add_argument(
    "--snapshot-meta-path",
    type=str,
    required=True,
    help="Input snapshot meta json path.",
  )
  parser.add_argument(
    "--rendered-prompts-dir",
    type=str,
    required=True,
    help="Output directory for rendered prompts jsonl files.",
  )

  parsed = parser.parse_args()

  prompts_root = parsed.prompts_root.strip()
  if not prompts_root:
    raise ValueError("prompts_root is empty.")

  prompt_paths = [p.strip() for p in parsed.prompt_paths if p and p.strip()]
  if not prompt_paths:
    raise ValueError("prompt_paths is empty.")

  samples_jsonl_path = parsed.samples_jsonl_path.strip()
  if not samples_jsonl_path:
    raise ValueError("samples_jsonl_path is empty.")

  snapshot_meta_path = parsed.snapshot_meta_path.strip()
  if not snapshot_meta_path:
    raise ValueError("snapshot_meta_path is empty.")

  rendered_prompts_dir = parsed.rendered_prompts_dir.strip()
  if not rendered_prompts_dir:
    raise ValueError("rendered_prompts_dir is empty.")

  return RenderPromptsCliArgs(
    prompts_root=prompts_root,
    prompt_paths=prompt_paths,
    samples_jsonl_path=samples_jsonl_path,
    rendered_prompts_dir=rendered_prompts_dir,
    snapshot_meta_path=snapshot_meta_path,
  )


def load_samples(samples_jsonl_path: str) -> list[SampleRecord]:
  """Load SampleRecord rows from a local snapshot jsonl."""
  sample_records: list[SampleRecord] = []
  for row in iter_rows_from_jsonl(
    samples_jsonl_path, required_keys=required_sample_keys
  ):
    sample_records.append(row)

  return sample_records


def render_and_write_one_prompt(
  *,
  prompts_root: str,
  prompt_path: str,
  rendered_prompts_dir: str,
  sample_records: list[SampleRecord],
  dataset_identifier: DatasetSnapshotIdentifier,
) -> str:
  """
  Render a single prompt template for all samples and write to a jsonl file.

  Output path:
    {rendered_prompts_dir}/{prompt_group_uid}/{prompt_version}.jsonl

  Returns:
    output jsonl path
  """
  prompt_group_uid, prompt_version = parse_prompt_path(prompt_path)
  full_prompt_path = str(Path(prompts_root) / prompt_path)
  template_text = load_prompt_text(full_prompt_path)

  out_path = str(
    Path(rendered_prompts_dir) / prompt_group_uid / f"{prompt_version}.jsonl"
  )
  ensure_parent_dir(out_path)

  with jsonlines.open(out_path, mode="w") as writer:
    for record in sample_records:
      rendered_prompt = render_prompt(
        template_text,
        input_text=record["input_text"],
        reference_output=record.get("reference_output"),
        output_text=None,
      )

      out_row: RenderedPrompt = {
        "dataset_group_uid": dataset_identifier["dataset_group_uid"],
        "dataset_version": dataset_identifier["dataset_version"],
        "split": dataset_identifier["split"],
        "prompt_group_uid": prompt_group_uid,
        "prompt_version": prompt_version,
        "prompt_path": prompt_path,
        "source_sample_id": record["source_sample_id"],
        "input_text": record["input_text"],
        "rendered_prompt": rendered_prompt,
      }
      if record.get("reference_output") is not None:
        out_row["reference_output"] = record["reference_output"]

      writer.write(out_row)

  return out_path


def render_prompts(args: RenderPromptsCliArgs) -> list[str]:
  """Render all prompt templates and write rendered prompts jsonl files."""
  sample_records = load_samples(args.samples_jsonl_path)
  dataset_meta: DatasetSnapshotMeta = read_json(args.snapshot_meta_path)
  dataset_identifier = extract_dataset_snapshot_identifier(dataset_meta)

  out_paths: list[str] = []
  for prompt_path in args.prompt_paths:
    out_paths.append(
      render_and_write_one_prompt(
        prompts_root=args.prompts_root,
        prompt_path=prompt_path,
        rendered_prompts_dir=args.rendered_prompts_dir,
        sample_records=sample_records,
        dataset_identifier=dataset_identifier,
      )
    )
  return out_paths


if __name__ == "__main__":
  args = parse_args()
  render_prompts(args)
