from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import jsonlines
from collections.abc import Iterable
from app.datasets.dataset_types import RawRow
import csv


def ensure_parent_dir(path: str) -> None:
  """
  Ensure the parent directory of `path` exists.

  This is a small helper to avoid repeating os.path.dirname + makedirs.
  """
  parent = Path(path).parent
  if str(parent) == ".":
    return
  parent.mkdir(parents=True, exist_ok=True)


def read_json(path: str) -> dict[str, Any]:
  """
  Read a .json file and return its parsed object as a dict.

  Raises:
    ValueError: if suffix is not .json.
    FileNotFoundError: if file does not exist.
    json.JSONDecodeError: if file content is invalid JSON.
  """
  file_path = Path(path)
  if file_path.suffix != ".json":
    raise ValueError(f"Invalid json path. Expected a .json file. Got: {path}")
  if not file_path.is_file():
    raise FileNotFoundError(f"JSON file not found: {path}")

  try:
    text = file_path.read_text(encoding="utf-8")
  except UnicodeDecodeError:
    text = file_path.read_text(encoding="utf-8-sig")

  res = json.loads(text)
  if not isinstance(res, dict):
    raise ValueError(
      f"Invalid json root. Expected an object/dict. Got: {type(res)}"
    )
  return res


def write_json(path: str, obj: Any) -> None:
  """
  Write `obj` to a .json file with stable formatting.

  Formatting:
    indent=2, ensure_ascii=False, sort_keys=True

  Raises:
    ValueError: if suffix is not .json.
  """
  file_path = Path(path)
  if file_path.suffix != ".json":
    raise ValueError(f"Invalid json path. Expected a .json file. Got: {path}")

  ensure_parent_dir(path)
  with file_path.open("w", encoding="utf-8") as file:
    json.dump(obj, file, indent=2, ensure_ascii=False, sort_keys=True)


def iter_rows_from_jsonl(
  input_path: str, required_keys: list[str] | None = None
) -> Iterable[RawRow]:
  path = Path(input_path)
  if path.suffix != ".jsonl":
    raise ValueError(
      f"Invalid dataset file. Expected a .jsonl file. Got: {input_path}"
    )
  if not path.is_file():
    raise FileNotFoundError(f"Dataset file not found: {input_path}")

  with jsonlines.open(input_path) as reader:
    for row in reader:
      if not isinstance(row, dict):
        raise ValueError("Each jsonl line must be a JSON object.")
      if required_keys is not None:
        for key in required_keys:
          if key not in row:
            raise ValueError(f"Missing required field: {key}")
      yield row


def iter_rows_from_csv(input_path: str) -> Iterable[RawRow]:
  path = Path(input_path)
  if path.suffix != ".csv":
    raise ValueError(
      f"Invalid dataset file. Expected a .csv file. Got: {input_path}"
    )
  if not path.is_file():
    raise FileNotFoundError(f"Dataset file not found: {input_path}")

  with path.open("r", newline="", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)
    for row in reader:
      yield row
