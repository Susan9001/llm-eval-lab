from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import jsonlines
from datetime import datetime, timezone
from pathlib import Path

from app.utils.file_io import ensure_parent_dir, write_json
from app.datasets.dataset_loader import (
  load_sample_records,
  preview_sample_records,
)

SampleRecord = dict[str, Any]


@dataclass(frozen=True)
class BuildArgs:
  input_path: str  # e.g. data/TruthfulQA.csv
  file_format: str  # "csv" | "jsonl"
  adapter_name: str  # "truthfulqa" | "generic" | ...
  out_jsonl_path: str  # e.g. data/snapshots/mini_truth.jsonl
  snapshot_meta_path: str | None  # e.g. data/snapshots/dataset_snapshot.json

  should_random_sample: bool
  limit: int | None
  seed: int | None

  preview_n: int  # default 3
  metadata_keys: list[str] | None  # If not provided, do not print metadata

  dataset_group_uid: str  # Required, globally unique
  dataset_display_name: str | None  # Optional, for display only
  dataset_version: str | None  # Optional
  split: str | None  # Optional, default "test"


def parse_args() -> BuildArgs:
  import argparse

  parser = argparse.ArgumentParser(
    description="Build dataset snapshot jsonl from a dataset file."
  )
  parser.add_argument(
    "--input-path", required=True, help="Input dataset file path."
  )
  parser.add_argument(
    "--format",
    required=True,
    choices=["csv", "jsonl"],
    help="Input file format.",
  )
  parser.add_argument(
    "--adapter", required=True, help="Adapter name, e.g. truthfulqa."
  )
  parser.add_argument(
    "--limit", type=int, default=None, help="Optional. Limit number of rows."
  )
  parser.add_argument(
    "--seed",
    type=int,
    default=None,
    help="Optional. Random seed for random sampling.",
  )
  parser.add_argument(
    "--should-random-sample",
    action="store_true",
    help="Optional. If set, shuffle with seed (if provided) then take first limit rows. Requires --limit.",
  )
  parser.add_argument(
    "--out-jsonl",
    required=True,
    help="Output jsonl path, e.g. data/snapshots/mini_truth.jsonl",
  )
  parser.add_argument(
    "--snapshot-meta",
    default=None,
    help="Optional. Output snapshot meta json path.",
  )
  parser.add_argument(
    "--preview-n", type=int, default=3, help="Preview first N sample records."
  )
  parser.add_argument(
    "--metadata-keys",
    nargs="+",
    default=None,
    help="Optional. Print these metadata keys in preview, e.g. --metadata-keys Type Category Source",
  )
  parser.add_argument(
    "--dataset-group-uid",
    required=True,
    help="Required. Unique dataset group uid in your system.",
  )
  parser.add_argument(
    "--dataset-display-name",
    default=None,
    help="Optional. Display name for humans.",
  )
  parser.add_argument(
    "--dataset-version", default=None, help="Optional. Dataset version string."
  )
  parser.add_argument(
    "--split", default="test", help='Optional. Default "test".'
  )

  args = parser.parse_args()
  file_format = args.format.strip().lower()
  adapter_name = args.adapter.strip().lower()
  if not adapter_name:
    raise ValueError("adapter_name is empty.")
  limit = args.limit
  if limit is not None and limit < 0:
    raise ValueError(f"limit must be >= 0, got {limit}")
  should_random_sample = bool(args.should_random_sample)
  seed = args.seed
  if should_random_sample and limit is None:
    raise ValueError(
      "When --should-random-sample is set, --limit must be provided."
    )
  if seed is not None and seed < 0:
    raise ValueError(f"seed must be >= 0, got {seed}")
  if seed is not None and not should_random_sample:
    raise ValueError(
      "seed is only meaningful with --should-random-sample. Either add --should-random-sample or remove --seed."
    )
  preview_n = args.preview_n
  if preview_n <= 0:
    raise ValueError(f"preview_n must be > 0, got {preview_n}")

  metadata_keys = args.metadata_keys
  if metadata_keys is not None:
    flattened: list[str] = []
    for key in metadata_keys:
      for part in key.split(","):
        part = part.strip()
        if part:
          flattened.append(part)
    metadata_keys = flattened if flattened else None

  dataset_group_uid = args.dataset_group_uid.strip()
  if not dataset_group_uid:
    raise ValueError("dataset_group_uid is empty.")

  dataset_display_name = (
    args.dataset_display_name.strip() if args.dataset_display_name else None
  )
  dataset_version = (
    args.dataset_version.strip() if args.dataset_version else None
  )
  split = args.split.strip() if args.split else None

  return BuildArgs(
    input_path=args.input_path,
    file_format=file_format,
    adapter_name=adapter_name,
    limit=limit,
    seed=seed,
    should_random_sample=should_random_sample,
    out_jsonl_path=args.out_jsonl,
    snapshot_meta_path=args.snapshot_meta,
    preview_n=preview_n,
    metadata_keys=metadata_keys,
    dataset_group_uid=dataset_group_uid,
    dataset_display_name=dataset_display_name,
    dataset_version=dataset_version,
    split=split,
  )


def build_snapshot(args: BuildArgs) -> None:
  """
  Main process entry point:
  - Generate jsonl snapshot of samples based on args configuration.
  - If snapshot meta path is specified, save snapshot meta in json format.
  """
  sample_records = load_sample_records(
    input_path=args.input_path,
    file_format=args.file_format,
    adapter_name=args.adapter_name,
    should_random_sample=args.should_random_sample,
    limit=args.limit,
    seed=args.seed,
  )
  ensure_parent_dir(args.out_jsonl_path)
  write_jsonl(args.out_jsonl_path, sample_records)

  if args.snapshot_meta_path:
    ensure_parent_dir(args.snapshot_meta_path)
    snap_meta = build_snapshot_meta(args, sample_records)
    write_json(args.snapshot_meta_path, snap_meta)
    print("****** metadata previews:")
    print(preview_snapshot_metadata(snap_meta))
    print()

  print("****** sample records previews:")
  print(
    preview_sample_records(
      sample_records, n=args.preview_n, metadata_keys=args.metadata_keys
    )
  )


def write_jsonl(out_path: str, sample_records: list[SampleRecord]) -> None:
  path = Path(out_path)
  if path.suffix != ".jsonl":
    raise ValueError(
      f"Invalid output file. Expected a .jsonl file. Got: {out_path}"
    )

  with jsonlines.open(str(path), mode="w") as writer:
    writer.write_all(sample_records)


def generate_version(
  should_random_sample: bool, limit: int | None, seed: int | None
) -> str:
  parts = [datetime.now().strftime("%Y-%m-%d")]
  if limit is not None:
    parts.append(f"limit{limit}")
  else:
    parts.append("all")
  if should_random_sample:
    if seed is not None:
      parts.append(f"seed{seed}")
    else:
      parts.append("seedNone")
  else:
    parts.append("head")
  return "_".join(parts)


def build_snapshot_meta(
  args: BuildArgs, sample_records: list[SampleRecord]
) -> dict[str, Any]:
  dataset_version = args.dataset_version
  if dataset_version is None:
    dataset_version = generate_version(
      args.should_random_sample, args.limit, args.seed
    )

  snapshot_meta = {
    "dataset_group_uid": args.dataset_group_uid,
    "adapter_name": args.adapter_name,
    "dataset_display_name": args.dataset_display_name,
    "dataset_version": dataset_version,
    "input_path": args.input_path,
    "file_format": args.file_format,
    "num_samples": len(sample_records),
    "split": args.split,
    "sampling": {
      "should_random_sample": args.should_random_sample,
      "limit": args.limit,
      "seed": args.seed,
    },
    "created_at": utc_now_iso8601(),
  }
  return snapshot_meta


def utc_now_iso8601() -> str:
  return (
    datetime.now(timezone.utc)
    .replace(microsecond=0)
    .isoformat()
    .replace("+00:00", "Z")
  )


def preview_snapshot_metadata(snap_meta: dict[str, Any]) -> str:
  rows: list[tuple[str, str]] = [
    ("dataset_group_uid", snap_meta.get("dataset_group_uid")),
    ("adapter_name", snap_meta.get("adapter_name")),
    ("dataset_display_name", str(snap_meta.get("dataset_display_name"))),
    ("dataset_version", snap_meta.get("dataset_version")),
    ("created_at", snap_meta.get("created_at")),
  ]

  key_width = max(len(key) for key, _ in rows)
  lines: list[str] = []
  for key, value in rows:
    lines.append(f"{key.ljust(key_width)} : {value}")
  return "\n".join(lines)


if __name__ == "__main__":
  args = parse_args()
  build_snapshot(args)
