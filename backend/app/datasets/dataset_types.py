from typing import Any, TypedDict


class SampleRecord(TypedDict, total=False):
  source_sample_id: str
  input_text: str
  reference_output: str | None
  # Optional, for supervised eval or curves. value should be 0 or 1 only.
  # Example: {"harmful": 0} or {"harmful": 1}
  labels: dict[str, int] | None
  metadata: dict[str, Any] | None


RawRow = dict[str, Any]


class SamplingMeta(TypedDict):
  """How a dataset snapshot was sampled."""

  should_random_sample: bool
  limit: int | None
  seed: int | None


class DatasetSnapshotIdentifier(TypedDict):
  """
  Minimal, stable dataset identity fields that downstream artifacts should carry.

  Use this in rendered_prompts.jsonl and model_outputs.jsonl so those artifacts
  are self-describing without depending on DB IDs.
  """

  dataset_group_uid: str
  dataset_version: str
  split: str


class DatasetSnapshotMeta(DatasetSnapshotIdentifier):
  """
  This is the single source of truth for snapshot provenance and how the
  snapshot was created.
  """

  adapter_name: str
  dataset_display_name: str | None

  input_path: str
  file_format: str
  num_samples: int

  sampling: SamplingMeta

  created_at: str  # ISO-8601 UTC timestamp (e.g. "2026-01-12T17:15:38Z")


def extract_dataset_snapshot_identifier(
  meta: DatasetSnapshotMeta,
) -> DatasetSnapshotIdentifier:
  """
  Extract minimal dataset identity info from full snapshot metadata.
  """
  return DatasetSnapshotIdentifier(
    dataset_group_uid=meta["dataset_group_uid"],
    dataset_version=meta["dataset_version"],
    split=meta["split"],
  )
