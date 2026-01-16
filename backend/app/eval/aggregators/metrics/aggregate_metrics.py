from __future__ import annotations

from collections.abc import Iterable
from collections import defaultdict
from dataclasses import asdict

from app.eval.eval_types import EvalResultRow
from app.eval.aggregators.metrics.metrics_types import (
  BucketBundle,
  CurvesBundle,
  MetricsBuildConfig,
  MetricsJson,
)
from app.eval.aggregators.metrics.bucket_accumulator import BucketAccumulator
from app.eval.aggregators.metrics.curves_accumulator import CurvesAccumulator


def build_metrics(
  eval_results_rows: Iterable[EvalResultRow],
  config: MetricsBuildConfig,
) -> MetricsJson:
  overall_bucket = BucketAccumulator()
  buckets_by_model_name: dict[str, BucketAccumulator] = defaultdict(
    BucketAccumulator
  )
  buckets_by_prompt_version: dict[str, BucketAccumulator] = defaultdict(
    BucketAccumulator
  )

  overall_curves = CurvesAccumulator()
  curves_by_model_name = defaultdict(CurvesAccumulator)
  curves_by_prompt_version = defaultdict(CurvesAccumulator)

  for row in eval_results_rows:
    model_name = row["model_name"]
    prompt_key = f"{row['prompt_group_uid']}:{row['prompt_version']}"

    overall_bucket.add(row, config)
    buckets_by_model_name[model_name].add(row, config)
    buckets_by_prompt_version[prompt_key].add(row, config)

    if config.include_curves:
      overall_curves.add(row, config)
      curves_by_model_name[model_name].add(row, config)
      curves_by_prompt_version[prompt_key].add(row, config)

  metrics_by_model_name = {
    k: acc.get_metrics() for k, acc in buckets_by_model_name.items()
  }
  metrics_by_prompt_version = {
    k: acc.get_metrics() for k, acc in buckets_by_prompt_version.items()
  }
  curves_metrics_by_model_name = {
    k: acc.get_metrics() for k, acc in curves_by_model_name.items()
  }
  curves_metrics_by_prompt_version = {
    k: acc.get_metrics() for k, acc in curves_by_prompt_version.items()
  }

  curves = None
  if config.include_curves:
    curves = CurvesBundle(
      overall=overall_curves.get_metrics(),
      by_model_name=curves_metrics_by_model_name,
      by_prompt_version=curves_metrics_by_prompt_version,
    )
  return MetricsJson(
    meta=asdict(config),
    summary=BucketBundle(
      overall=overall_bucket.get_metrics(),
      by_model_name=metrics_by_model_name,
      by_prompt_version=metrics_by_prompt_version,
    ),
    curves=curves,
  )
