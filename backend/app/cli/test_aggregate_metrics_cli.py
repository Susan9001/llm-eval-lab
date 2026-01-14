from __future__ import annotations

import json

import pytest

from app.cli.aggregate_metrics_cli import MetricsCliArgs, run_metrics


def _write_jsonl(path: str, rows: list[dict[str, object]]) -> None:
  with open(path, "w", encoding="utf-8") as f:
    for row in rows:
      f.write(json.dumps(row, ensure_ascii=False) + "\n")


def test_aggregate_metrics_cli_end_to_end(tmp_path) -> None:
  eval_results_path = str(tmp_path / "eval_results.jsonl")
  metrics_path = str(tmp_path / "metrics.json")

  # 4 rows total
  # generation: 3 succeeded, 1 failed
  # eval: 3 succeeded with valid score, 1 failed
  # threshold = 0.5, pass scores: 1.0, 0.5 => 2/3
  rows: list[dict[str, object]] = [
    {
      "dataset_group_uid": "truthfulqa",
      "dataset_version": "v1",
      "split": "validation",
      "prompt_group_uid": "truthfulqa_prompt",
      "prompt_version": "v1",
      "source_sample_id": "1",
      "model_output_uuid": "mo_1",
      "provider": "openai",
      "model_name": "gpt-test-1",
      "generation_status": "SUCCEEDED",
      "generation_error_message": None,
      "judge_type": "rule",
      "judge_name": "rule_judge",
      "judge_version": None,
      "eval_status": "SUCCEEDED",
      "eval_error_message": None,
      "rule_outcomes": {
        "exact_match": {"status": "SUCCEEDED", "score": 1.0},
      },
      "started_at": "2026-01-14T00:00:00Z",
      "finished_at": "2026-01-14T00:00:01Z",
      "latency_ms": 1000,
    },
    {
      "dataset_group_uid": "truthfulqa",
      "dataset_version": "v1",
      "split": "validation",
      "prompt_group_uid": "truthfulqa_prompt",
      "prompt_version": "v1",
      "source_sample_id": "2",
      "model_output_uuid": "mo_2",
      "provider": "openai",
      "model_name": "gpt-test-1",
      "generation_status": "SUCCEEDED",
      "generation_error_message": None,
      "judge_type": "rule",
      "judge_name": "rule_judge",
      "judge_version": None,
      "eval_status": "SUCCEEDED",
      "eval_error_message": None,
      "rule_outcomes": {
        "exact_match": {"status": "SUCCEEDED", "score": 0.5},
      },
      "started_at": "2026-01-14T00:00:00Z",
      "finished_at": "2026-01-14T00:00:01Z",
      "latency_ms": 1000,
    },
    {
      "dataset_group_uid": "truthfulqa",
      "dataset_version": "v1",
      "split": "validation",
      "prompt_group_uid": "truthfulqa_prompt",
      "prompt_version": "v2",
      "source_sample_id": "3",
      "model_output_uuid": "mo_3",
      "provider": "openai",
      "model_name": "gpt-test-2",
      "generation_status": "FAILED",
      "generation_error_message": "rate_limited",
      "judge_type": "rule",
      "judge_name": "rule_judge",
      "judge_version": None,
      "eval_status": "FAILED",
      "eval_error_message": "no_output",
      "rule_outcomes": {},
      "started_at": "2026-01-14T00:00:00Z",
      "finished_at": "2026-01-14T00:00:01Z",
      "latency_ms": None,
    },
    {
      "dataset_group_uid": "truthfulqa",
      "dataset_version": "v1",
      "split": "validation",
      "prompt_group_uid": "truthfulqa_prompt",
      "prompt_version": "v2",
      "source_sample_id": "4",
      "model_output_uuid": "mo_4",
      "provider": "openai",
      "model_name": "gpt-test-2",
      "generation_status": "SUCCEEDED",
      "generation_error_message": None,
      "judge_type": "rule",
      "judge_name": "rule_judge",
      "judge_version": None,
      "eval_status": "SUCCEEDED",
      "eval_error_message": None,
      "rule_outcomes": {
        "exact_match": {"status": "SUCCEEDED", "score": 0.2},
      },
      "started_at": "2026-01-14T00:00:00Z",
      "finished_at": "2026-01-14T00:00:01Z",
      "latency_ms": 1000,
    },
  ]

  _write_jsonl(eval_results_path, rows)

  args = MetricsCliArgs(
    eval_results_path=eval_results_path,
    metrics_path=metrics_path,
    primary_score_rule="exact_match",
    threshold=0.5,
  )

  run_metrics(args)

  with open(metrics_path, "r", encoding="utf-8") as f:
    metrics = json.load(f)

  assert "meta" in metrics
  assert metrics["meta"]["primary_score_rule"] == "exact_match"
  assert metrics["meta"]["threshold"] == 0.5
  assert isinstance(metrics["meta"]["generated_at"], str)
  assert metrics["meta"]["generated_at"].endswith("Z")

  assert "overall" in metrics
  overall = metrics["overall"]
  assert overall["num_total"] == 4
  assert overall["num_generation_succeeded"] == 3
  assert overall["num_generation_failed"] == 1
  assert overall["num_eval_succeeded"] == 3
  assert overall["num_eval_failed"] == 1

  assert overall["pass_rate"] == pytest.approx(2 / 3, rel=1e-9)
  assert overall["avg_score"] == pytest.approx((1.0 + 0.5 + 0.2) / 3, rel=1e-9)

  assert "by_model_name" in metrics
  assert set(metrics["by_model_name"].keys()) == {"gpt-test-1", "gpt-test-2"}

  assert "by_prompt_version" in metrics
  # key format: prompt_group_uid:prompt_version
  assert set(metrics["by_prompt_version"].keys()) == {
    "truthfulqa_prompt:v1",
    "truthfulqa_prompt:v2",
  }

  assert "curves" in metrics
  assert "roc" in metrics["curves"]
  assert "pr" in metrics["curves"]
