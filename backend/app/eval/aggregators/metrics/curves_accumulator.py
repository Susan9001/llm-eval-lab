from __future__ import annotations

from dataclasses import dataclass, field
from math import inf

from app.common.statuses import EVAL_STATUS_SUCCEEDED, RULE_STATUS_SUCCEEDED
from app.eval.eval_types import EvalResultRow
from app.eval.aggregators.metrics.metrics_types import (
  CurvesMetrics,
  MetricsBuildConfig,
)


def _as_binary_label(value: object) -> int | None:
  if isinstance(value, bool):
    return 1 if value else 0
  if isinstance(value, int):
    return value if value in (0, 1) else None
  if isinstance(value, float):
    return int(value) if value in (0.0, 1.0) else None
  if isinstance(value, str) and value in ("0", "1"):
    return int(value)
  return None


def _trapz_auc(xs: list[float], ys: list[float]) -> float:
  # Trapezoidal rule. Assumes xs are monotonic.
  if len(xs) != len(ys) or len(xs) < 2:
    return 0.0

  area = 0.0
  for i in range(1, len(xs)):
    x0, x1 = xs[i - 1], xs[i]
    y0, y1 = ys[i - 1], ys[i]
    area += (x1 - x0) * (y0 + y1) / 2.0
  return float(area)


def _empty_curves(
  num_labeled: int,
  num_labeled_pos: int,
  num_labeled_neg: int,
) -> CurvesMetrics:
  return CurvesMetrics(
    num_labeled=num_labeled,
    num_labeled_pos=num_labeled_pos,
    num_labeled_neg=num_labeled_neg,
    roc=dict(fprs=[], tprs=[], thresholds=[]),
    pr=dict(precisions=[], recalls=[], thresholds=[]),
    roc_auc=None,
    pr_auc=None,
  )


@dataclass
class CurvesAccumulator:
  """Internal accumulator for building CurvesMetrics.

  Bucketing (overall / by_model_name / by_prompt_version) should be done by
  the caller (e.g. build_metrics). This accumulator only tracks one bucket.

  Skip rules are kept consistent with the prior build_curves implementation:
  - eval_status must be SUCCEEDED
  - primary_score_rule outcome must exist and be SUCCEEDED
  - outcome.score must be numeric
  - labels[config.binary_label_key] must be convertible to a binary label
  """

  # threshold -> [num_labeled_pos, num_labeled_neg]
  threshold_counts: dict[float, list[int]] = field(default_factory=dict)

  num_labeled: int = 0
  num_labeled_pos: int = 0
  num_labeled_neg: int = 0

  def add(self, row: EvalResultRow, config: MetricsBuildConfig) -> None:
    if (
      not config.binary_label_key
      or row.get("eval_status") != EVAL_STATUS_SUCCEEDED
    ):
      return

    outcome = (row.get("rule_outcomes") or {}).get(config.primary_score_rule)
    if not outcome or outcome.get("status") != RULE_STATUS_SUCCEEDED:
      return

    threshold = outcome.get("score")
    if not isinstance(threshold, (int, float)):
      return

    labels = row.get("labels") or {}
    label = _as_binary_label(labels.get(config.binary_label_key))
    if label is None:
      return

    threshold = float(threshold)

    self.num_labeled += 1
    if label == 1:
      self.num_labeled_pos += 1
    else:
      self.num_labeled_neg += 1

    counts = self.threshold_counts.get(threshold)
    if counts is None:
      counts = [0, 0]
      self.threshold_counts[threshold] = counts

    # counts[0] = labeled_pos, counts[1] = labeled_neg
    if label == 1:
      counts[0] += 1
    else:
      counts[1] += 1

  def get_metrics(self) -> CurvesMetrics:
    # Need both classes for meaningful ROC/PR curves.
    if (
      self.num_labeled == 0
      or self.num_labeled_pos == 0
      or self.num_labeled_neg == 0
    ):
      return _empty_curves(
        self.num_labeled, self.num_labeled_pos, self.num_labeled_neg
      )

    # Sweep thresholds in descending order: as threshold decreases, predicted-positive grows.
    thresholds_sorted = sorted(self.threshold_counts.keys(), reverse=True)

    tp = 0
    fp = 0

    roc_fprs: list[float] = [0.0]
    roc_tprs: list[float] = [0.0]

    pr_precisions: list[float] = [1.0]
    pr_recalls: list[float] = [0.0]

    thresholds: list[float] = [inf]

    for threshold in thresholds_sorted:
      labeled_pos, labeled_neg = self.threshold_counts[threshold]
      tp += labeled_pos
      fp += labeled_neg

      tpr = tp / float(self.num_labeled_pos)
      fpr = fp / float(self.num_labeled_neg)

      pred_pos = tp + fp
      precision = (tp / pred_pos) if pred_pos > 0 else 1.0
      recall = tpr

      roc_fprs.append(float(fpr))
      roc_tprs.append(float(tpr))

      pr_precisions.append(float(precision))
      pr_recalls.append(float(recall))

      thresholds.append(float(threshold))

    roc_auc = _trapz_auc(roc_fprs, roc_tprs)
    pr_auc = _trapz_auc(pr_recalls, pr_precisions)

    return CurvesMetrics(
      num_labeled=self.num_labeled,
      num_labeled_pos=self.num_labeled_pos,
      num_labeled_neg=self.num_labeled_neg,
      roc=dict(fprs=roc_fprs, tprs=roc_tprs, thresholds=thresholds),
      pr=dict(
        precisions=pr_precisions, recalls=pr_recalls, thresholds=thresholds
      ),
      roc_auc=roc_auc,
      pr_auc=pr_auc,
    )
