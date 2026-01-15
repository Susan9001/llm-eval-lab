from __future__ import annotations

from dataclasses import dataclass
from app.common.statuses import (
  EVAL_STATUS_SUCCEEDED,
  GENERATION_STATUS_SUCCEEDED,
)
from app.eval.aggregators.metrics.metrics_types import (
  BucketMetrics,
  MetricsBuildConfig,
)
from app.eval.eval_types import EvalResultRow


@dataclass
class BucketAccumulator:
  """
  Internal accumulator for building BucketMetrics.
  """

  num_total: int = 0

  num_generation_succeeded: int = 0
  num_generation_failed: int = 0

  num_eval_succeeded: int = 0
  num_eval_failed: int = 0
  num_primary_scored: int = 0

  num_positive: int = 0  # tp + fp
  sum_score: float = 0.0

  def add(self, row: EvalResultRow, config: MetricsBuildConfig) -> None:
    self.num_total += 1

    generation_status = row.get("generation_status")
    if generation_status == GENERATION_STATUS_SUCCEEDED:
      self.num_generation_succeeded += 1
    else:
      self.num_generation_failed += 1

    eval_status = row.get("eval_status")

    primary_score: float | None = None
    primary_outcome = row.get("rule_outcomes", {}).get(
      config.primary_score_rule
    )
    if primary_outcome is not None:
      raw_score = primary_outcome.get("score")
      if isinstance(raw_score, (int, float)):
        primary_score = float(raw_score)

    if eval_status == EVAL_STATUS_SUCCEEDED:
      self.num_eval_succeeded += 1
      if primary_score is not None:
        self.num_primary_scored += 1
        self.sum_score += primary_score
        if primary_score >= config.threshold:
          self.num_positive += 1
    else:
      self.num_eval_failed += 1

  def get_metrics(self) -> BucketMetrics:
    positive_rate = 0.0
    avg_score: float | None = None

    if self.num_primary_scored > 0:
      positive_rate = self.num_positive / self.num_primary_scored
      avg_score = self.sum_score / self.num_primary_scored

    return BucketMetrics(
      num_total=self.num_total,
      num_generation_succeeded=self.num_generation_succeeded,
      num_generation_failed=self.num_generation_failed,
      num_eval_succeeded=self.num_eval_succeeded,
      num_eval_failed=self.num_eval_failed,
      num_primary_scored=self.num_primary_scored,
      positive_rate=positive_rate,
      avg_score=avg_score,
    )
