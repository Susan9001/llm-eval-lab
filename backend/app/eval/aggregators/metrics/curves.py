from __future__ import annotations

from app.eval.aggregators.metrics.metrics_types import CurvesMetrics


def build_curves_placeholder() -> CurvesMetrics:
  res: CurvesMetrics = {
    "roc": {"fprs": [], "tprs": [], "thresholds": []},
    "pr": {"precisions": [], "recalls": [], "thresholds": []},
  }
  return res
