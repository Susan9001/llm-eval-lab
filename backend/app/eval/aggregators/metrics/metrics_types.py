from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


class BucketMetrics(TypedDict):
  """
  Metrics bucket schema.

  Used by:
  - overall
  - by_model_name[model_name]
  - by_prompt_version[prompt_group_uid:prompt_version]
  """

  num_total: int

  num_generation_succeeded: int
  num_generation_failed: int

  num_eval_succeeded: int
  num_eval_failed: int
  num_primary_scored: int
  num_over_threshold: int = 0

  num_labeled: int = 0  # with valid 0/1 label in EvalResultRow
  num_labeled_pos: int = 0
  num_labeled_neg: int = 0

  tp: int = 0
  fp: int = 0
  tn: int = 0
  fn: int = 0

  avg_score: float | None
  over_threshold_rate: float | None

  # supervised metrics (None when num_labeled == 0)
  # (tp + tn) / (tp + tn + fp + fn)
  accuracy: float | None
  # tp / (tp + fp), None if no positive prediction.
  precision: float | None
  # tp / (tp + fn), None if no positive label.
  recall: float | None
  # 2PR / (P + R), None if precision or recall is None.
  f1: float | None


class CurvesMetrics(TypedDict):
  """
  Curves schema.

  If data is insufficient, arrays should be empty but keys must exist.

  Expected keys:
  - roc: fprs, tprs, thresholds
  - pr: precisions, recalls, thresholds
  """

  roc: dict[str, list[float]]  # fprs, tprs, thresholds
  pr: dict[str, list[float]]  # precisions, recalls, thresholds
  roc_auc: float | None
  pr_auc: float | None
  num_labeled: int
  num_labeled_pos: int
  num_labeled_neg: int


class BucketBundle(TypedDict):
  overall: BucketMetrics
  by_model_name: dict[str, BucketMetrics]
  by_prompt_version: dict[str, BucketMetrics]


class CurvesBundle(TypedDict):
  overall: CurvesMetrics
  by_model_name: dict[str, CurvesMetrics]  # can be empty dict
  by_prompt_version: dict[str, CurvesMetrics]  # can be empty dict


class MetricsJson(TypedDict):
  meta: dict[str, object]
  summary: BucketBundle
  curves: CurvesBundle | None


@dataclass(frozen=True)
class MetricsBuildConfig:
  generated_at: str
  threshold: float
  primary_score_rule: str

  binary_label_key: str | None = None
  include_curves: bool = False
