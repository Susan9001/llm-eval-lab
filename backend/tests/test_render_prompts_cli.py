import json
from pathlib import Path

from app.cli.render_prompts_cli import (
  RenderPromptsCliArgs,
  render_and_write_one_prompt,
  render_prompts,
)


def _write_snapshot_meta(tmp_path: Path) -> Path:
  """
  Write a minimal-but-valid dataset_snapshot.json based on our DatasetSnapshotMeta contract.
  """
  snapshot_meta = {
    "dataset_group_uid": "truthfulqa",
    "adapter_name": "truthfulqa",
    "dataset_display_name": "TruthfulQA (mini)",
    "dataset_version": "2026-01-12_limit80_head",
    "input_path": "data/raw/truthfulqa.csv",
    "file_format": "csv",
    "num_samples": 2,
    "split": "test",
    "sampling": {
      "should_random_sample": False,
      "limit": 2,
      "seed": None,
    },
    "created_at": "2026-01-12T17:15:38Z",
  }

  path = tmp_path / "dataset_snapshot.json"
  path.write_text(json.dumps(snapshot_meta), encoding="utf-8")
  return path


def test_render_and_write_one_prompt_writes_jsonl(tmp_path: Path) -> None:
  prompts_root = tmp_path / "prompts"
  (prompts_root / "truthfulqa_generation_base").mkdir(parents=True)
  (prompts_root / "truthfulqa_generation_base" / "v1.txt").write_text(
    "Q: {input_text}\n",
    encoding="utf-8",
  )

  rendered_prompts_dir = tmp_path / "rendered"

  sample_records = [
    {
      "source_sample_id": "id_1",
      "input_text": "hello",
      "reference_output": "world",
      "metadata": None,
    },
    {
      "source_sample_id": "id_2",
      "input_text": "foo",
      "reference_output": None,
      "metadata": None,
    },
  ]

  dataset_identifier = {
    "dataset_group_uid": "truthfulqa",
    "dataset_version": "2026-01-12_limit80_head",
    "split": "test",
  }

  out_path = render_and_write_one_prompt(
    prompts_root=str(prompts_root),
    prompt_path="truthfulqa_generation_base/v1.txt",
    rendered_prompts_dir=str(rendered_prompts_dir),
    sample_records=sample_records,
    dataset_identifier=dataset_identifier,
  )

  out_file = Path(out_path)
  assert out_file.is_file()

  lines = out_file.read_text(encoding="utf-8").splitlines()
  assert len(lines) == 2

  row1 = json.loads(lines[0])
  assert row1["prompt_group_uid"] == "truthfulqa_generation_base"
  assert row1["prompt_version"] == "v1"
  assert row1["prompt_path"] == "truthfulqa_generation_base/v1.txt"
  assert row1["source_sample_id"] == "id_1"
  assert row1["rendered_prompt"] == "Q: hello\n"

  row2 = json.loads(lines[1])
  assert row2["source_sample_id"] == "id_2"
  assert row2["rendered_prompt"] == "Q: foo\n"


def test_render_prompts_end_to_end_includes_snapshot_identifier(
  tmp_path: Path,
) -> None:
  prompts_root = tmp_path / "prompts"
  (prompts_root / "truthfulqa_generation_base").mkdir(parents=True)
  (prompts_root / "truthfulqa_generation_base" / "v1.txt").write_text(
    "Q1: {input_text}\n",
    encoding="utf-8",
  )
  (prompts_root / "truthfulqa_generation_base" / "v2.txt").write_text(
    "Q2: {input_text}\n",
    encoding="utf-8",
  )

  samples_jsonl_path = tmp_path / "mini_truth.jsonl"
  samples_jsonl_path.write_text(
    json.dumps({"source_sample_id": "id_1", "input_text": "hello"})
    + "\n"
    + json.dumps({"source_sample_id": "id_2", "input_text": "foo"})
    + "\n",
    encoding="utf-8",
  )

  snapshot_meta_path = _write_snapshot_meta(tmp_path)

  rendered_prompts_dir = tmp_path / "rendered"

  args = RenderPromptsCliArgs(
    prompts_root=str(prompts_root),
    prompt_paths=[
      "truthfulqa_generation_base/v1.txt",
      "truthfulqa_generation_base/v2.txt",
    ],
    samples_jsonl_path=str(samples_jsonl_path),
    snapshot_meta_path=str(snapshot_meta_path),
    rendered_prompts_dir=str(rendered_prompts_dir),
  )

  out_paths = render_prompts(args)
  assert len(out_paths) == 2

  v1_path = rendered_prompts_dir / "truthfulqa_generation_base" / "v1.jsonl"
  v2_path = rendered_prompts_dir / "truthfulqa_generation_base" / "v2.jsonl"
  assert v1_path.is_file()
  assert v2_path.is_file()

  # Validate the snapshot identifier fields exist in each output row.
  v1_row1 = json.loads(v1_path.read_text(encoding="utf-8").splitlines()[0])
  v2_row1 = json.loads(v2_path.read_text(encoding="utf-8").splitlines()[0])

  for row in (v1_row1, v2_row1):
    assert row["dataset_group_uid"] == "truthfulqa"
    assert row["dataset_version"] == "2026-01-12_limit80_head"
    assert row["split"] == "test"

  assert v1_row1["rendered_prompt"].startswith("Q1:")
  assert v2_row1["rendered_prompt"].startswith("Q2:")
