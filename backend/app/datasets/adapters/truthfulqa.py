from app.datasets.dataset_types import SampleRecord, RawRow
from hashlib import sha1
import re
from typing import Any

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


def adapt_truthfulqa_row(row: RawRow, row_index: int) -> SampleRecord:
  """Map a row of TruthfulQA csv to SampleRecord."""
  validate_truthfulqa_columns(row)
  return SampleRecord(
    source_sample_id=build_source_sample_id(row, row_index),
    input_text=row["Question"],
    reference_output=row.get(reference_col, None),
    metadata=extract_metadata(row),
  )


def build_source_sample_id(row: RawRow, row_index: int) -> str:
  """Generate a stable source_sample_id. Simplest is to use row_index, more robust to add question hash."""
  question = row["Question"]
  normalized_question = re.sub(r"\s+", " ", question.strip())
  question_hash = sha1(normalized_question.encode("utf-8")).hexdigest()[:16]
  return question_hash + "_" + str(row_index)


def parse_answers_field(text: str | None) -> list[str]:
  """Split fields like Correct Answers or Incorrect Answers into a list."""
  if not text:
    return []
  parts = [part.strip() for part in text.split(";")]
  return [part for part in parts if part]


def extract_metadata(row: RawRow) -> dict[str, Any]:
  """Extract type, category, source_url, correct_answers, incorrect_answers, etc. into metadata."""
  metadata = {}
  for key, val in row.items():
    if key in metadata_cols and val is not None:
      if key in answers_cols:
        metadata[key] = parse_answers_field(val)
      else:
        metadata[key] = val

  return metadata


def validate_truthfulqa_columns(row: RawRow) -> None:
  """可选。检查必须列是否存在，不存在就 raise，方便早期排错。"""
  for key in required_cols:
    if key not in row or row[key] is None:
      raise ValueError(f"Column {key} not exists. Current keys: {row.keys()}")
