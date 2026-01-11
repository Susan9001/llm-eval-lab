import json
import re
from pathlib import Path
from datetime import datetime

import pytest

from app.datasets.build_dataset_snapshot import (
  BuildArgs,
  build_snapshot_meta,
  generate_version,
  write_jsonl,
  write_snapshot_meta,
)


def test_generate_version_fixed_date(monkeypatch: pytest.MonkeyPatch) -> None:
  import app.datasets.build_dataset_snapshot as bds

  class FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
      return datetime(2026, 1, 11, 0, 0, 0, tzinfo=tz)

  monkeypatch.setattr(bds, "datetime", FixedDatetime)

  res = generate_version(should_random_sample=False, limit=80, seed=None)
  assert res == "2026-01-11_limit80_head"


def test_build_snapshot_meta_with_provided_dataset_version() -> None:
  args = BuildArgs(
    input_path="data/TruthfulQA.csv",
    file_format="csv",
    adapter_name="truthfulqa",
    out_jsonl_path="data/snapshots/mini_truth.jsonl",
    snapshot_meta_path=None,
    should_random_sample=False,
    limit=10,
    seed=None,
    preview_n=3,
    metadata_keys=None,
    dataset_group_uid="truthfulqa",
    dataset_display_name="TruthfulQA",
    dataset_version="v1_manual",
    split="test",
  )

  snap_meta = build_snapshot_meta(args, sample_records=[{"input_text": "x"}])
  assert snap_meta["dataset_version"] == "v1_manual"


def test_build_snapshot_meta_with_autogenerates() -> None:
  args = BuildArgs(
    input_path="data/TruthfulQA.csv",
    file_format="csv",
    adapter_name="truthfulqa",
    out_jsonl_path="data/snapshots/mini_truth.jsonl",
    snapshot_meta_path=None,
    should_random_sample=True,
    limit=5,
    seed=42,
    preview_n=3,
    metadata_keys=None,
    dataset_group_uid="truthfulqa",
    dataset_display_name=None,
    dataset_version=None,
    split="test",
  )

  snap_meta = build_snapshot_meta(args, sample_records=[{"input_text": "x"}])

  assert isinstance(snap_meta["dataset_version"], str)
  assert snap_meta["dataset_version"] != ""

  created_at = snap_meta["created_at"]
  assert isinstance(created_at, str)
  assert created_at.endswith("Z")
  assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", created_at)


def test_write_snapshot_meta_roundtrip(tmp_path: Path) -> None:
  meta_path = tmp_path / "dataset_snapshot.json"
  snap_meta = {
    "dataset_group_uid": "truthfulqa",
    "adapter_name": "truthfulqa",
    "dataset_display_name": "TruthfulQA",
    "dataset_version": "v1",
    "created_at": "2026-01-11T00:00:00Z",
  }

  write_snapshot_meta(str(meta_path), snap_meta)
  loaded = json.loads(meta_path.read_text(encoding="utf-8"))
  assert loaded == snap_meta


def test_write_jsonl_roundtrip(tmp_path: Path) -> None:
  out_path = tmp_path / "mini_truth.jsonl"
  sample_records = [{"input_text": "a"}, {"input_text": "b"}]

  write_jsonl(str(out_path), sample_records)

  lines = out_path.read_text(encoding="utf-8").splitlines()
  assert len(lines) == 2
  assert json.loads(lines[0])["input_text"] == "a"
  assert json.loads(lines[1])["input_text"] == "b"
