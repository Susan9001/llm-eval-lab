from typing import NotRequired, TypedDict

from app.datasets.dataset_types import DatasetSnapshotIdentifier


class PromptIdentifier(TypedDict):
  """
  Stable prompt identity fields.

  prompt_path is provenance only, not required for joining.
  """

  prompt_group_uid: str
  prompt_version: str


class RenderedPromptIdentifier(PromptIdentifier, DatasetSnapshotIdentifier):
  """
  Stable rendered prompt identity fields, including both dataset snapshot
  identifier, initial prompt identity and source_sample_id.
  """

  source_sample_id: str


class RenderedPrompt(RenderedPromptIdentifier):
  input_text: str | None
  rendered_prompt: str
  reference_output: NotRequired[str]
  prompt_path: str | None
