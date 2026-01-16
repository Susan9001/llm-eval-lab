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
  num_over_threshold: int = 0
  sum_score: float = 0.0

  # Supervised classification accounting (requires labels)
  num_labeled: int = 0
  num_labeled_pos: int = 0
  num_labeled_neg: int = 0

  tp: int = 0
  fp: int = 0
  tn: int = 0
  fn: int = 0

  def add(self, row: EvalResultRow, config: MetricsBuildConfig) -> None:
    self.num_total += 1

    generation_status = row.get("generation_status")
    if generation_status == GENERATION_STATUS_SUCCEEDED:
      self.num_generation_succeeded += 1
    else:
      self.num_generation_failed += 1

    eval_status = row.get("eval_status")
    if eval_status != EVAL_STATUS_SUCCEEDED:
      self.num_eval_failed += 1
      return
    self.num_eval_succeeded += 1

    # Primary score
    primary_score: float | None = None
    primary_outcome = (row.get("rule_outcomes") or {}).get(
      config.primary_score_rule
    )
    if primary_outcome is not None:
      raw_score = primary_outcome.get("score")
      if isinstance(raw_score, (int, float)):
        primary_score = float(raw_score)

    if primary_score is None:
      return

    self.num_primary_scored += 1
    self.sum_score += primary_score
    pred = int(primary_score >= config.threshold)
    if pred:
      self.num_over_threshold += 1

    # Confusion matrix only if label is available.
    labels = row.get("labels") or {}
    label = labels.get(config.binary_label_key)
    if label not in (0, 1):
      return
    self.num_labeled += 1
    if label == 1:
      self.num_labeled_pos += 1
    else:
      self.num_labeled_neg += 1
    if label == 1 and pred == 1:
      self.tp += 1
    elif label == 1 and pred == 0:
      self.fn += 1
    elif label == 0 and pred == 1:
      self.fp += 1
    else:
      self.tn += 1

  def get_metrics(self) -> BucketMetrics:
    avg_score: float | None = None
    over_threshold_rate = 0.0

    if self.num_primary_scored > 0:
      avg_score = self.sum_score / self.num_primary_scored
      over_threshold_rate = self.num_over_threshold / self.num_primary_scored

    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None

    if self.num_labeled > 0:
      accuracy = (self.tp + self.tn) / self.num_labeled

      pred_pos = self.tp + self.fp
      if pred_pos > 0:
        precision = self.tp / pred_pos

      labeled_pos = self.tp + self.fn
      if labeled_pos > 0:
        recall = self.tp / labeled_pos

      if (
        precision is not None
        and recall is not None
        and (precision + recall) > 0
      ):
        f1 = 2 * precision * recall / (precision + recall)

    # Note: keep legacy fields (num_pass/pass_rate) for backward compatibility.
    return BucketMetrics(
      num_total=self.num_total,
      num_generation_succeeded=self.num_generation_succeeded,
      num_generation_failed=self.num_generation_failed,
      num_eval_succeeded=self.num_eval_succeeded,
      num_eval_failed=self.num_eval_failed,
      num_primary_scored=self.num_primary_scored,
      num_over_threshold=self.num_over_threshold,
      over_threshold_rate=over_threshold_rate,
      avg_score=avg_score,
      num_labeled=self.num_labeled,
      num_labeled_pos=self.num_labeled_pos,
      num_labeled_neg=self.num_labeled_neg,
      tp=self.tp,
      fp=self.fp,
      tn=self.tn,
      fn=self.fn,
      accuracy=accuracy,
      precision=precision,
      recall=recall,
      f1=f1,
    )
