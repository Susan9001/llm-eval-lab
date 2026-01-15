from __future__ import annotations

from pathlib import Path
import re

from app.datasets.dataset_types import DatasetSnapshotIdentifier, SampleRecord
from app.prompts.prompt_types import RenderedPrompt


_GROUP_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def parse_prompt_path(prompt_path: str) -> tuple[str, str]:
  """
  Parse a relative prompt path like "truthfulqa_generation_base/v1.txt".

  Returns:
    (prompt_group_uid, prompt_version)
  """
  path = Path(prompt_path)
  if path.suffix != ".txt":
    raise ValueError(
      f"Invalid prompt_path. Expected a .txt file. Got: {prompt_path}"
    )
  if len(path.parts) < 2:
    raise ValueError(
      "Invalid prompt_path. Expected at least one parent directory so we can derive prompt_group_uid. "
      f"Got: {prompt_path}"
    )

  prompt_version = path.stem
  prompt_group_uid = "_".join(path.parts[:-1])

  if not _GROUP_RE.fullmatch(prompt_group_uid):
    raise ValueError(
      "Invalid prompt_group_uid derived from prompt_path. Expected lowercase snake_case matching "
      "[a-z][a-z0-9_]*. "
      f"Got: {prompt_group_uid} (from {prompt_path})"
    )

  return prompt_group_uid, prompt_version


def load_prompt_text(prompt_path: str) -> str:
  path = Path(prompt_path)
  if path.suffix != ".txt":
    raise ValueError(
      f"Invalid prompt_path. Expected a .txt file. Got: {prompt_path}"
    )
  if not path.is_file():
    raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

  try:
    return path.read_text(encoding="utf-8")
  except UnicodeDecodeError:
    return path.read_text(encoding="utf-8-sig")


def render_prompt(
  template_text: str,
  *,
  input_text: str,
  reference_output: str | None = None,
  output_text: str | None = None,
) -> str:
  """
  Render prompt by simple string replacement.

  Supported placeholders:
    {input_text}, {reference_output}, {output_text}
  """
  rendered = template_text

  if "{input_text}" in rendered:
    rendered = rendered.replace("{input_text}", input_text)

  if "{reference_output}" in rendered:
    if reference_output is None:
      raise ValueError(
        "Prompt template contains {reference_output}, but reference_output is None."
      )
    rendered = rendered.replace("{reference_output}", reference_output)

  if "{output_text}" in rendered:
    if output_text is None:
      raise ValueError(
        "Prompt template contains {output_text}, but output_text is None."
      )
    rendered = rendered.replace("{output_text}", output_text)

  return rendered


def render_one_prompt(
  template_text: str,
  prompt_group_uid: str,
  prompt_version: str,
  dataset_identifier: DatasetSnapshotIdentifier,
  sample_record: SampleRecord,
  *,
  prompt_path: str | None,
  output_text: str | None = None,
) -> RenderedPrompt:
  """
  Render a single prompt for one sample record.

  Returns:
    RenderedPrompt dict
  """
  input_text = sample_record["input_text"]
  reference_output = sample_record.get("reference_output")
  labels = sample_record.get("labels")

  rendered_prompt = render_prompt(
    template_text,
    input_text=input_text,
    reference_output=reference_output,
    output_text=output_text,
  )

  out_row: RenderedPrompt = {
    "dataset_group_uid": dataset_identifier["dataset_group_uid"],
    "dataset_version": dataset_identifier["dataset_version"],
    "split": dataset_identifier["split"],
    "prompt_group_uid": prompt_group_uid,
    "prompt_version": prompt_version,
    "source_sample_id": sample_record["source_sample_id"],
    "input_text": input_text,
    "rendered_prompt": rendered_prompt,
    "reference_output": reference_output,
  }
  if prompt_path is not None:
    out_row["prompt_path"] = prompt_path
  if reference_output is not None:
    out_row["reference_output"] = reference_output
  if labels is not None:
    out_row["labels"] = labels

  return out_row
