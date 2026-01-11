import json
from pathlib import Path

import pytest

from app.datasets.dataset_loader import (
  apply_sampling,
  load_sample_records,
)


def test_apply_sampling_random_requires_limit() -> None:
  items = list(range(10))
  with pytest.raises(ValueError):
    apply_sampling(items, should_random_sample=True, limit=None, seed=42)


def test_apply_sampling_head_all() -> None:
  items = list(range(5))
  res = apply_sampling(items, should_random_sample=False, limit=None, seed=None)
  assert res == [0, 1, 2, 3, 4]


def test_apply_sampling_head_keeps_order() -> None:
  items = list(range(10))
  res = apply_sampling(items, should_random_sample=False, limit=5, seed=None)
  assert res == [0, 1, 2, 3, 4]


def test_apply_sampling_random_is_deterministic() -> None:
  items = list(range(100))
  res1 = apply_sampling(items, should_random_sample=True, limit=10, seed=7)
  res2 = apply_sampling(items, should_random_sample=True, limit=10, seed=7)
  assert res1 == res2

  res3 = apply_sampling(items, should_random_sample=True, limit=10, seed=8)
  assert res1 != res3


def test_load_sample_records_csv_smoke(tmp_path: Path) -> None:
  csv_path = tmp_path / "demo.csv"
  csv_path.write_text(
    "Question,Best Answer,Type,Category,Source\n"
    "What is 2+2?,4,Math,Arithmetic,unit_test\n",
    encoding="utf-8",
  )

  sample_records = load_sample_records(
    input_path=str(csv_path),
    file_format="csv",
    adapter_name="truthfulqa",
    should_random_sample=False,
    limit=10,
    seed=None,
  )

  assert len(sample_records) == 1
  record = sample_records[0]
  assert record.get("source_sample_id") is not None
  assert record.get("input_text") == "What is 2+2?"
  assert record.get("reference_output") == "4"
  assert record.get("metadata") is not None


def test_load_sample_records_jsonl_with_monkeypatched_adapter(
  tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
  jsonl_path = tmp_path / "demo.jsonl"
  jsonl_path.write_text(
    json.dumps({"x": 1}) + "\n" + json.dumps({"x": 2}) + "\n",
    encoding="utf-8",
  )

  import app.datasets.dataset_loader as dataset_loader

  def adapter(row: dict, row_index: int) -> dict:
    return {
      "source_sample_id": f"id_{row_index}",
      "input_text": str(row.get("x")),
      "reference_output": None,
      "metadata": {"x": row.get("x")},
    }

  monkeypatch.setattr(dataset_loader, "get_adapter", lambda _: adapter)

  sample_records = load_sample_records(
    input_path=str(jsonl_path),
    file_format="jsonl",
    adapter_name="whatever",
    should_random_sample=False,
    limit=None,
    seed=None,
  )
  assert [r["source_sample_id"] for r in sample_records] == ["id_1", "id_2"]
