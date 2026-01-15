from __future__ import annotations

import pytest

from app.common.statuses import (
  EVAL_STATUS_SUCCEEDED,
  GENERATION_STATUS_FAILED,
  GENERATION_STATUS_SUCCEEDED,
  RULE_STATUS_SUCCEEDED,
)
from app.eval.aggregators.metrics.bucket_accumulator import BucketAccumulator
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
  generation_status: str = GENERATION_STATUS_SUCCEEDED,
  eval_status: str = EVAL_STATUS_SUCCEEDED,
  rule_outcomes: dict | None = None,
) -> dict:
  row = {
    "dataset_group_uid": "dg",
    "dataset_version": "v1",
    "split": "test",
    "source_sample_id": "s1",
    "prompt_group_uid": "pg",
    "prompt_version": "p1",
    "prompt_path": None,
    "model_output_uuid": "uuid-1",
    "provider": "mock",
    "model_name": "mock-1",
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


def test_empty_accumulator():
  acc = BucketAccumulator()
  metrics = acc.get_metrics()

  assert metrics["num_total"] == 0
  assert metrics["num_generation_succeeded"] == 0
  assert metrics["num_generation_failed"] == 0
  assert metrics["num_eval_succeeded"] == 0
  assert metrics["num_eval_failed"] == 0
  assert metrics["num_primary_scored"] == 0
  assert metrics["positive_rate"] == 0.0
  assert metrics["avg_score"] is None


def test_single_row_eval_succeeded_pass():
  config = make_config(threshold=0.5)
  acc = BucketAccumulator()

  row = make_row(
    rule_outcomes={"rule1": make_rule_outcome(0.8)},
  )
  acc.add(row, config)

  assert acc.num_total == 1
  assert acc.num_generation_succeeded == 1
  assert acc.num_generation_failed == 0
  assert acc.num_eval_succeeded == 1
  assert acc.num_eval_failed == 0
  assert acc.num_primary_scored == 1
  assert acc.num_positive == 1
  assert acc.sum_score == 0.8

  metrics = acc.get_metrics()
  assert metrics["positive_rate"] == 1.0
  assert metrics["avg_score"] == 0.8


def test_single_row_eval_succeeded_no_pass():
  config = make_config(threshold=0.5)
  acc = BucketAccumulator()

  row = make_row(
    rule_outcomes={"rule1": make_rule_outcome(0.3)},
  )
  acc.add(row, config)

  assert acc.num_total == 1
  assert acc.num_generation_succeeded == 1
  assert acc.num_eval_succeeded == 1
  assert acc.num_eval_failed == 0
  assert acc.num_primary_scored == 1
  assert acc.num_positive == 0
  assert acc.sum_score == 0.3

  metrics = acc.get_metrics()
  assert metrics["positive_rate"] == 0.0
  assert metrics["avg_score"] == 0.3


def test_single_row_generation_failed():
  config = make_config()
  acc = BucketAccumulator()

  row = make_row(
    generation_status=GENERATION_STATUS_FAILED,
    eval_status="FAILED",  # When generation fails, eval also fails
  )
  acc.add(row, config)

  assert acc.num_total == 1
  assert acc.num_generation_succeeded == 0
  assert acc.num_generation_failed == 1
  assert acc.num_eval_succeeded == 0
  assert acc.num_eval_failed == 1
  assert acc.num_primary_scored == 0


def test_single_row_eval_failed_no_primary_score():
  config = make_config()
  acc = BucketAccumulator()

  row = make_row(rule_outcomes={})
  acc.add(row, config)

  assert acc.num_total == 1
  assert acc.num_generation_succeeded == 1
  assert acc.num_generation_failed == 0
  assert acc.num_eval_succeeded == 1  # eval_status is SUCCEEDED
  assert acc.num_eval_failed == 0
  assert acc.num_primary_scored == 0  # but no primary_score


def test_single_row_empty_rule_outcomes():
  config = make_config()
  acc = BucketAccumulator()

  row = make_row(rule_outcomes=None)
  acc.add(row, config)

  assert acc.num_eval_succeeded == 1  # eval_status is SUCCEEDED
  assert acc.num_eval_failed == 0
  assert acc.num_primary_scored == 0  # but no primary_score


def test_single_row_primary_score_rule_not_exist():
  config = make_config(primary_score_rule="rule1")
  acc = BucketAccumulator()

  row = make_row(rule_outcomes={"rule2": make_rule_outcome(0.8)})
  acc.add(row, config)

  assert acc.num_eval_succeeded == 1  # eval_status is SUCCEEDED
  assert acc.num_eval_failed == 0
  assert acc.num_primary_scored == 0  # but primary_score_rule doesn't exist


def test_single_row_score_equals_threshold_passes():
  config = make_config(threshold=0.5)
  acc = BucketAccumulator()

  row = make_row(rule_outcomes={"rule1": make_rule_outcome(0.5)})
  acc.add(row, config)

  assert acc.num_positive == 1
  assert acc.num_eval_succeeded == 1
  assert acc.num_primary_scored == 1


def test_multiple_rows_mixed():
  config = make_config(threshold=0.5)
  acc = BucketAccumulator()

  # Pass: 0.8 >= 0.5
  acc.add(make_row(rule_outcomes={"rule1": make_rule_outcome(0.8)}), config)
  # No pass: 0.3 < 0.5
  acc.add(make_row(rule_outcomes={"rule1": make_rule_outcome(0.3)}), config)
  # No pass: 0.5 == 0.5 (edge case, passes)
  acc.add(make_row(rule_outcomes={"rule1": make_rule_outcome(0.5)}), config)
  # Generation failed (eval_status = FAILED)
  acc.add(
    make_row(
      generation_status=GENERATION_STATUS_FAILED,
      eval_status="FAILED",
    ),
    config,
  )
  # Eval succeeded but no primary_score (empty rule_outcomes)
  acc.add(make_row(rule_outcomes={}), config)

  assert acc.num_total == 5
  assert acc.num_generation_succeeded == 4
  assert acc.num_generation_failed == 1
  assert acc.num_eval_succeeded == 4  # All except generation failed
  assert acc.num_eval_failed == 1  # Only generation failed
  assert acc.num_primary_scored == 3  # Only rows with valid scores
  assert acc.num_positive == 2  # 0.8 and 0.5
  assert acc.sum_score == pytest.approx(1.6)  # 0.8 + 0.3 + 0.5

  metrics = acc.get_metrics()
  assert metrics["positive_rate"] == pytest.approx(2 / 3)
  assert metrics["avg_score"] == pytest.approx(1.6 / 3)


def test_get_metrics_with_zero_eval_succeeded():
  config = make_config()
  acc = BucketAccumulator()

  # Add only failed rows - use eval_status="FAILED" to ensure eval doesn't succeed
  acc.add(
    make_row(rule_outcomes={}, eval_status="FAILED"),
    config,
  )
  acc.add(
    make_row(
      generation_status=GENERATION_STATUS_FAILED,
      eval_status="FAILED",
    ),
    config,
  )

  metrics = acc.get_metrics()
  assert metrics["num_total"] == 2
  assert metrics["num_eval_succeeded"] == 0  # No eval succeeded
  assert metrics["num_primary_scored"] == 0  # No primary scores
  assert metrics["positive_rate"] == 0.0
  assert metrics["avg_score"] is None
