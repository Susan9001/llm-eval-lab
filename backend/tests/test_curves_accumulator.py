from __future__ import annotations


from app.common.statuses import (
  EVAL_STATUS_FAILED,
  EVAL_STATUS_SUCCEEDED,
  GENERATION_STATUS_SUCCEEDED,
  RULE_STATUS_SUCCEEDED,
)
from app.eval.aggregators.metrics.curves_accumulator import CurvesAccumulator
from app.eval.aggregators.metrics.metrics_types import MetricsBuildConfig


def make_config(*, primary_score_rule: str = "rule1") -> MetricsBuildConfig:
  return MetricsBuildConfig(
    generated_at="2024-01-01T00:00:00Z",
    threshold=0.5,
    primary_score_rule=primary_score_rule,
    binary_label_key="harmful",
    include_curves=False,
  )


def make_row(
  *,
  eval_status: str = EVAL_STATUS_SUCCEEDED,
  rule_outcomes: dict | None = None,
  labels: dict | None = None,
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
    "generation_status": GENERATION_STATUS_SUCCEEDED,
    "generation_error_message": None,
    "judge_type": "rule",
    "judge_name": "rule_judge",
    "judge_version": None,
    "eval_status": eval_status,
    "eval_error_message": None,
    "rule_outcomes": rule_outcomes or {},
    "labels": labels or {},
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
  acc = CurvesAccumulator()
  metrics = acc.get_metrics()

  assert metrics["num_labeled"] == 0
  assert metrics["num_labeled_pos"] == 0
  assert metrics["num_labeled_neg"] == 0
  assert metrics["roc"]["fprs"] == []
  assert metrics["roc"]["tprs"] == []
  assert metrics["roc"]["thresholds"] == []
  assert metrics["pr"]["precisions"] == []
  assert metrics["pr"]["recalls"] == []
  assert metrics["pr"]["thresholds"] == []
  assert metrics["roc_auc"] is None
  assert metrics["pr_auc"] is None


def test_row_with_eval_failed_is_skipped():
  config = make_config()
  acc = CurvesAccumulator()

  row = make_row(
    eval_status=EVAL_STATUS_FAILED,
    rule_outcomes={"rule1": make_rule_outcome(0.8)},
    labels={"harmful": 1},
  )
  acc.add(row, config)

  metrics = acc.get_metrics()
  assert metrics["num_labeled"] == 0


def test_row_without_primary_score_is_skipped():
  config = make_config()
  acc = CurvesAccumulator()

  row = make_row(
    rule_outcomes={},
    labels={"harmful": 1},
  )
  acc.add(row, config)

  metrics = acc.get_metrics()
  assert metrics["num_labeled"] == 0


def test_row_without_label_is_skipped():
  config = make_config()
  acc = CurvesAccumulator()

  row = make_row(
    rule_outcomes={"rule1": make_rule_outcome(0.8)},
    labels={},
  )
  acc.add(row, config)

  metrics = acc.get_metrics()
  assert metrics["num_labeled"] == 0


def test_row_with_invalid_label_is_skipped():
  config = make_config()
  acc = CurvesAccumulator()

  row = make_row(
    rule_outcomes={"rule1": make_rule_outcome(0.8)},
    labels={"harmful": 2},  # Invalid label
  )
  acc.add(row, config)

  metrics = acc.get_metrics()
  assert metrics["num_labeled"] == 0


def test_single_class_only_positive():
  config = make_config()
  acc = CurvesAccumulator()

  for _ in range(3):
    row = make_row(
      rule_outcomes={"rule1": make_rule_outcome(0.8)},
      labels={"harmful": 1},
    )
    acc.add(row, config)

  metrics = acc.get_metrics()
  assert metrics["num_labeled"] == 3
  assert metrics["num_labeled_pos"] == 3
  assert metrics["num_labeled_neg"] == 0
  # Empty curves when only one class
  assert metrics["roc"]["fprs"] == []
  assert metrics["roc"]["tprs"] == []
  assert metrics["roc_auc"] is None
  assert metrics["pr_auc"] is None


def test_single_class_only_negative():
  config = make_config()
  acc = CurvesAccumulator()

  for _ in range(3):
    row = make_row(
      rule_outcomes={"rule1": make_rule_outcome(0.3)},
      labels={"harmful": 0},
    )
    acc.add(row, config)

  metrics = acc.get_metrics()
  assert metrics["num_labeled"] == 3
  assert metrics["num_labeled_pos"] == 0
  assert metrics["num_labeled_neg"] == 3
  # Empty curves when only one class
  assert metrics["roc"]["fprs"] == []
  assert metrics["roc"]["tprs"] == []
  assert metrics["roc_auc"] is None
  assert metrics["pr_auc"] is None


def test_perfect_classifier():
  config = make_config()
  acc = CurvesAccumulator()

  # Perfect separation: positive samples have higher scores
  for _ in range(2):
    row = make_row(
      rule_outcomes={"rule1": make_rule_outcome(0.9)},
      labels={"harmful": 1},
    )
    acc.add(row, config)

  for _ in range(2):
    row = make_row(
      rule_outcomes={"rule1": make_rule_outcome(0.3)},
      labels={"harmful": 0},
    )
    acc.add(row, config)

  metrics = acc.get_metrics()
  assert metrics["num_labeled"] == 4
  assert metrics["num_labeled_pos"] == 2
  assert metrics["num_labeled_neg"] == 2
  # Perfect classifier should have AUC = 1.0
  assert metrics["roc_auc"] == 1.0
  assert metrics["pr_auc"] == 1.0


def test_binary_label_various_types():
  config = make_config()
  acc = CurvesAccumulator()

  # Test various binary label formats
  for label in [1, 0, True, False, "1", "0"]:
    row = make_row(
      rule_outcomes={"rule1": make_rule_outcome(0.5)},
      labels={"harmful": label},
    )
    acc.add(row, config)

  metrics = acc.get_metrics()
  assert metrics["num_labeled"] == 6
  assert metrics["num_labeled_pos"] == 3
  assert metrics["num_labeled_neg"] == 3


def test_curve_points_structure():
  config = make_config()
  acc = CurvesAccumulator()

  # Add some mixed data
  acc.add(
    make_row(
      rule_outcomes={"rule1": make_rule_outcome(0.9)}, labels={"harmful": 1}
    ),
    config,
  )
  acc.add(
    make_row(
      rule_outcomes={"rule1": make_rule_outcome(0.8)}, labels={"harmful": 1}
    ),
    config,
  )
  acc.add(
    make_row(
      rule_outcomes={"rule1": make_rule_outcome(0.3)}, labels={"harmful": 0}
    ),
    config,
  )
  acc.add(
    make_row(
      rule_outcomes={"rule1": make_rule_outcome(0.2)}, labels={"harmful": 0}
    ),
    config,
  )

  metrics = acc.get_metrics()
  # Check that arrays have same length
  assert len(metrics["roc"]["fprs"]) == len(metrics["roc"]["tprs"])
  assert len(metrics["roc"]["fprs"]) == len(metrics["roc"]["thresholds"])
  assert len(metrics["pr"]["precisions"]) == len(metrics["pr"]["recalls"])
  assert len(metrics["pr"]["precisions"]) == len(metrics["pr"]["thresholds"])

  # Check ROC starts at (0,0)
  assert metrics["roc"]["fprs"][0] == 0.0
  assert metrics["roc"]["tprs"][0] == 0.0

  # Check PR starts at (recall=0, precision=1)
  assert metrics["pr"]["recalls"][0] == 0.0
  assert metrics["pr"]["precisions"][0] == 1.0

  # AUCs should be valid
  assert 0.0 <= metrics["roc_auc"] <= 1.0
  assert 0.0 <= metrics["pr_auc"] <= 1.0
