from typing import NotRequired

from app.datasets.dataset_types import DatasetSnapshotIdentifier


class RenderedPrompt(DatasetSnapshotIdentifier):
  prompt_group_uid: str
  prompt_version: str
  prompt_path: str | None

  source_sample_id: str
  input_text: str | None
  rendered_prompt: str

  reference_output: NotRequired[str]
