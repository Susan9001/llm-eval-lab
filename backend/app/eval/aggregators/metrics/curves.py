from __future__ import annotations

from app.eval.aggregators.metrics.metrics_types import CurvesMetrics
from app.eval.eval_types import EvalResultRow
from app.eval.aggregators.metrics.metrics_types import MetricsBuildConfig


def build_curves(
  eval_results_rows: list[EvalResultRow], config: MetricsBuildConfig
) -> CurvesMetrics:
  """Return an empty curves object with all expected keys.

  This keeps downstream JSON schema stable when curves cannot be computed yet.
  """

  return {
    "roc": {"fprs": [], "tprs": [], "thresholds": []},
    "pr": {"precisions": [], "recalls": [], "thresholds": []},
    "roc_auc": None,
    "pr_auc": None,
    "num_labeled": 0,
    "num_labeled_pos": 0,
    "num_labeled_neg": 0,
  }
