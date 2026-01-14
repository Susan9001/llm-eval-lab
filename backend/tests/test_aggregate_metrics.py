from __future__ import annotations

from app.common.statuses import (
  EVAL_STATUS_SUCCEEDED,
  GENERATION_STATUS_SUCCEEDED,
  RULE_STATUS_SUCCEEDED,
)
from app.eval.aggregators.metrics.aggregate_metrics import build_metrics
from app.eval.aggregators.metrics.metrics_types import MetricsBuildConfig


def make_config(
  *, threshold: float = 0.5, primary_score_rule: str = "rule1"
) -> MetricsBuildConfig:
  return MetricsBuildConfig(
    generated_at="2024-01-01T00:00:00Z",
    threshold=threshold,
    primary_score_rule=primary_score_rule,
  )


def make_row(
  *,
  model_name: str = "mock-1",
  prompt_group_uid: str = "pg",
  prompt_version: str = "p1",
  generation_status: str = GENERATION_STATUS_SUCCEEDED,
  eval_status: str = EVAL_STATUS_SUCCEEDED,
  rule_outcomes: dict | None = None,
) -> dict:
  row = {
    "dataset_group_uid": "dg",
    "dataset_version": "v1",
    "split": "test",
    "source_sample_id": "s1",
    "prompt_group_uid": prompt_group_uid,
    "prompt_version": prompt_version,
    "prompt_path": None,
    "model_output_uuid": "uuid-1",
    "provider": "mock",
    "model_name": model_name,
    "generation_status": generation_status,
    "generation_error_message": None,
    "judge_type": "rule",
    "judge_name": "rule_judge",
    "judge_version": None,
    "eval_status": eval_status,
    "eval_error_message": None,
    "rule_outcomes": rule_outcomes or {},
    "started_at": "2024-01-01T00:00:00Z",
    "finished_at": "2024-01-01T00:00:01Z",
    "latency_ms": 1000,
  }
  return row


def make_rule_outcome(score: float) -> dict:
  return {
    "status": RULE_STATUS_SUCCEEDED,
    "score": score,
    "rationale": None,
    "error_message": None,
  }


def test_build_metrics_empty_input():
  config = make_config()
  result = build_metrics([], config)

  assert result["meta"]["generated_at"] == "2024-01-01T00:00:00Z"
  assert result["meta"]["threshold"] == 0.5
  assert result["meta"]["primary_score_rule"] == "rule1"

  assert result["overall"]["num_total"] == 0
  assert result["by_model_name"] == {}
  assert result["by_prompt_version"] == {}
  assert result["curves"]["roc"] == {"fprs": [], "tprs": [], "thresholds": []}
  assert result["curves"]["pr"] == {
    "precisions": [],
    "recalls": [],
    "thresholds": [],
  }


def test_build_metrics_single_row():
  config = make_config()
  row = make_row(rule_outcomes={"rule1": make_rule_outcome(0.8)})

  result = build_metrics([row], config)

  # Overall
  assert result["overall"]["num_total"] == 1
  assert result["overall"]["num_eval_succeeded"] == 1
  assert result["overall"]["pass_rate"] == 1.0
  assert result["overall"]["avg_score"] == 0.8

  # By model name
  assert "mock-1" in result["by_model_name"]
  assert result["by_model_name"]["mock-1"]["num_total"] == 1

  # By prompt version
  assert "pg:p1" in result["by_prompt_version"]
  assert result["by_prompt_version"]["pg:p1"]["num_total"] == 1


def test_build_metrics_multiple_rows_different_models():
  config = make_config()
  rows = [
    make_row(
      model_name="model-a",
      prompt_group_uid="pg",
      prompt_version="p1",
      rule_outcomes={"rule1": make_rule_outcome(0.7)},
    ),
    make_row(
      model_name="model-b",
      prompt_group_uid="pg",
      prompt_version="p1",
      rule_outcomes={"rule1": make_rule_outcome(0.3)},
    ),
    make_row(
      model_name="model-a",
      prompt_group_uid="pg",
      prompt_version="p2",
      rule_outcomes={"rule1": make_rule_outcome(0.9)},
    ),
  ]

  result = build_metrics(rows, config)

  # Overall: 3 rows, 2 passed (0.7 and 0.9)
  assert result["overall"]["num_total"] == 3
  assert result["overall"]["pass_rate"] == 2 / 3

  # By model name
  assert len(result["by_model_name"]) == 2
  assert result["by_model_name"]["model-a"]["num_total"] == 2
  assert result["by_model_name"]["model-b"]["num_total"] == 1

  # By prompt version
  assert len(result["by_prompt_version"]) == 2
  assert result["by_prompt_version"]["pg:p1"]["num_total"] == 2
  assert result["by_prompt_version"]["pg:p2"]["num_total"] == 1


def test_build_metrics_with_failed_rows():
  config = make_config()
  rows = [
    make_row(rule_outcomes={"rule1": make_rule_outcome(0.8)}),
    make_row(generation_status="FAILED"),
    make_row(rule_outcomes={}),
  ]

  result = build_metrics(rows, config)

  # Overall: 3 total, 1 eval succeeded
  assert result["overall"]["num_total"] == 3
  assert result["overall"]["num_generation_succeeded"] == 2
  assert result["overall"]["num_generation_failed"] == 1
  assert result["overall"]["num_eval_succeeded"] == 1
  assert result["overall"]["num_eval_failed"] == 2
