from hashlib import sha1
import re
from typing import Any

from app.datasets.dataset_types import RawRow, SampleRecord


required_cols = {"Question"}
metadata_cols = {
  "Type",
  "Category",
  "Source",
  "Incorrect Answers",
  "Correct Answers",
}
answers_cols = {"Incorrect Answers", "Correct Answers"}
reference_col = "Best Answer"


class TruthfulQAAdapter:
  """Adapter for TruthfulQA dataset format."""

  name = "truthfulqa"

  def adapt(self, row: RawRow, row_index: int) -> SampleRecord:
    """Map a row of TruthfulQA csv to SampleRecord."""
    self._validate_columns(row)
    return SampleRecord(
      source_sample_id=self._build_source_sample_id(row, row_index),
      input_text=row["Question"],
      reference_output=row.get(reference_col, None),
      metadata=self._extract_metadata(row),
    )

  def _build_source_sample_id(self, row: RawRow, row_index: int) -> str:
    """Generate a stable source_sample_id."""
    question = row["Question"]
    normalized_question = re.sub(r"\s+", " ", question.strip())
    question_hash = sha1(normalized_question.encode("utf-8")).hexdigest()[:16]
    return question_hash + "_" + str(row_index)

  def _parse_answers_field(self, text: str | None) -> list[str]:
    """Split fields like Correct Answers or Incorrect Answers into a list."""
    if not text:
      return []
    parts = [part.strip() for part in text.split(";")]
    return [part for part in parts if part]

  def _extract_metadata(self, row: RawRow) -> dict[str, Any]:
    """Extract type, category, source_url, correct_answers, incorrect_answers, etc."""
    metadata = {}
    for key, val in row.items():
      if key in metadata_cols and val is not None:
        if key in answers_cols:
          metadata[key] = self._parse_answers_field(val)
        else:
          metadata[key] = val
    return metadata

  def _validate_columns(self, row: RawRow) -> None:
    """Check that required columns exist."""
    for key in required_cols:
      if key not in row or row[key] is None:
        raise ValueError(f"Column {key} not exists. Current keys: {row.keys()}")
