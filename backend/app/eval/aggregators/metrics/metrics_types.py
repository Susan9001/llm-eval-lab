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

  pass_rate: float
  avg_score: float | None


class CurvesMetrics(TypedDict):
  """
  Curves schema.

  If data is insufficient, arrays should be empty but keys must exist.

  Expected keys:
  - roc: fprs, tprs, thresholds
  - pr: precisions, recalls, thresholds
  """

  roc: dict[str, list[float]]
  pr: dict[str, list[float]]


class MetricsJson(TypedDict):
  meta: dict[str, object]
  overall: BucketMetrics
  by_model_name: dict[str, BucketMetrics]
  by_prompt_version: dict[str, BucketMetrics]
  curves: CurvesMetrics


@dataclass(frozen=True)
class MetricsBuildConfig:
  generated_at: str
  threshold: float
  primary_score_rule: str

  def to_meta(self) -> dict[str, object]:
    return {
      "generated_at": self.generated_at,
      "threshold": self.threshold,
      "primary_score_rule": self.primary_score_rule,
    }
