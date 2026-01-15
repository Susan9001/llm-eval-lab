from __future__ import annotations

from hashlib import sha1
import re
from typing import Any

from app.datasets.dataset_types import RawRow, SampleRecord


_REQUIRED_COLS = {"text", "harmful"}


class AgNewsHarmfulAdapter:
  """
  Adapter for agnews_harmful_01.csv.

  Expected columns:
  1. text: str
  2. harmful: 0/1 (int or str)
  3. label: optional, original AG News label (0-3), stored into metadata
  """

  def adapt(self, row: RawRow, row_index: int) -> SampleRecord:
    self._validate_columns(row)

    text = self._coerce_str(row["text"])
    harmful = self._parse_binary_label(row["harmful"], col_name="harmful")

    labels = {"harmful": harmful}

    metadata: dict[str, Any] = {}
    if "label" in row and row["label"] is not None:
      metadata["ag_news_label"] = self._parse_int(
        row["label"], col_name="label"
      )

    res: SampleRecord = SampleRecord(
      source_sample_id=self._build_source_sample_id(
        text=text, row_index=row_index
      ),
      input_text=text,
      reference_output=None,
      labels=labels,
      metadata=metadata or None,
    )
    return res

  def _validate_columns(self, row: RawRow) -> None:
    missing_cols = [
      col for col in _REQUIRED_COLS if col not in row or row[col] is None
    ]
    if missing_cols:
      raise ValueError(
        f"Missing required columns: {missing_cols}. Current keys: {sorted(row.keys())}"
      )

  def _build_source_sample_id(self, text: str, row_index: int) -> str:
    normalized_text = re.sub(r"\s+", " ", text.strip())
    text_hash = sha1(normalized_text.encode("utf-8")).hexdigest()[:16]
    return text_hash + "_" + str(row_index)

  def _coerce_str(self, value: Any) -> str:
    if value is None:
      return ""
    if isinstance(value, str):
      return value
    return str(value)

  def _parse_int(self, value: Any, col_name: str) -> int:
    if isinstance(value, bool):
      return 1 if value else 0
    if isinstance(value, int):
      return value
    if isinstance(value, float):
      if value.is_integer():
        return int(value)
      raise ValueError(
        f"Column {col_name} must be int-like, got float: {value}"
      )
    if isinstance(value, str):
      value_str = value.strip()
      if value_str == "":
        raise ValueError(f"Column {col_name} is empty string")
      try:
        return int(value_str)
      except ValueError as exc:
        raise ValueError(
          f"Column {col_name} must be int, got: {value}"
        ) from exc
    raise ValueError(f"Column {col_name} must be int, got type: {type(value)}")

  def _parse_binary_label(self, value: Any, col_name: str) -> int:
    num = self._parse_int(value, col_name=col_name)
    if num not in (0, 1):
      raise ValueError(f"Column {col_name} must be 0 or 1, got: {num}")
    return num
