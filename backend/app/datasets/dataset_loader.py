from typing import TypeVar
from collections.abc import Iterable
import random

from app.datasets.dataset_types import SampleRecord, RawRow
from app.datasets.adapters.base import build_dataset_adapter
from app.utils.file_io import iter_rows_from_jsonl, iter_rows_from_csv


T = TypeVar("T")


def load_sample_records(
  input_path: str,
  file_format: str,
  adapter_name: str,
  should_random_sample: bool,
  limit: int | None,
  seed: int | None,
) -> list[SampleRecord]:
  """Main entry point: read rows, apply adapter, sample, return sample_records."""
  rows: Iterable[RawRow] = []
  if file_format == "csv":
    rows = iter_rows_from_csv(input_path)
  elif file_format == "jsonl":
    rows = iter_rows_from_jsonl(input_path)
  else:
    raise ValueError(f"Invalid file format {file_format}")

  idx_rows = list(enumerate(rows, start=1))
  idx_rows = apply_sampling(idx_rows, should_random_sample, limit, seed)

  adapter = build_dataset_adapter(adapter_name)
  records = []
  for idx, row in idx_rows:
    records.append(adapter.adapt(row, idx))
  return records


def apply_sampling(
  items: list[T],
  should_random_sample: bool,
  limit: int | None,
  seed: int | None,
) -> list[T]:
  """
  Rules:
  1. If limit is None and should_random_sample is False: return all items, no shuffle, seed is ignored.
  2. If limit is None and should_random_sample is True: raise exception, because if sampling, limit must be specified.
  3. If limit is not None and should_random_sample is False: return first limit items, no shuffle, seed is ignored.
  4. If limit is not None and should_random_sample is True: shuffle with seed (optional) then take first limit items.
  """
  if limit is None:
    if should_random_sample:
      raise ValueError("For random sampling, limit should not be None.")
    return items

  if limit < 0:
    raise ValueError(f"Limit must be >= 0, got {limit}")

  if not should_random_sample:
    return items[:limit]

  targets = items.copy()
  rand = random.Random(seed)
  rand.shuffle(targets)
  return targets[:limit]


def preview_sample_records(
  sample_records: list[SampleRecord],
  n: int = 3,
  *,
  metadata_keys: list[str] | None = None,
) -> str:
  """
  General preview output:
  1. Always print Total and Preview.
  2. For each item: print source_sample_id, whether ref exists, truncated input_text.
  3. Only print metadata key-value pairs when metadata_keys is specified.
  """
  total = len(sample_records)
  if total == 0:
    return "Total: 0\nPreview: 0"

  preview_n = min(n, total)
  lines: list[str] = []
  lines.append(f"Total: {total}")
  lines.append(f"Preview: {preview_n}")

  def truncate_text(text: str, max_len: int = 120) -> str:
    text = " ".join(text.split())
    if len(text) <= max_len:
      return text
    return text[: max_len - 3] + "..."

  def format_meta_value(value: object, max_len: int = 80) -> str:
    text = repr(value)
    if len(text) <= max_len:
      return text
    return text[: max_len - 3] + "..."

  for i in range(preview_n):
    sample_record = sample_records[i]
    source_sample_id = sample_record.get("source_sample_id")
    input_text = sample_record.get("input_text") or ""
    reference_output = sample_record.get("reference_output")
    metadata = sample_record.get("metadata") or {}

    ref_flag = "Y" if reference_output else "N"

    meta_text = ""
    if metadata_keys is not None:
      meta_parts: list[str] = []
      for key in metadata_keys:
        if key in metadata and metadata[key] is not None:
          meta_parts.append(f"{key}={format_meta_value(metadata[key])}")
      meta_text = (
        " meta={" + ", ".join(meta_parts) + "}" if meta_parts else " meta={}"
      )

    lines.append(
      f'{i + 1}) id={source_sample_id} ref={ref_flag} input="{truncate_text(input_text)}"{meta_text}'
    )

  return "\n".join(lines)
