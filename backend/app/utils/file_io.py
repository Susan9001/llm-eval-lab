from __future__ import annotations

from pathlib import Path
from typing import Any
import json


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
