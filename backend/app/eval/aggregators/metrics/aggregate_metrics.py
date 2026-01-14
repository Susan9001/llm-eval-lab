from __future__ import annotations

from collections.abc import Iterable
from collections import defaultdict

from app.eval.eval_types import EvalResultRow
from app.eval.aggregators.metrics.metrics_types import (
  MetricsBuildConfig,
  MetricsJson,
)
from app.eval.aggregators.metrics.bucket_accumulator import BucketAccumulator
from app.eval.aggregators.metrics.curves import build_curves_placeholder


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

  for row in eval_results_rows:
    overall_bucket.add(row, config)

    model_name = row["model_name"]
    buckets_by_model_name[model_name].add(row, config)

    prompt_key = f"{row['prompt_group_uid']}:{row['prompt_version']}"
    buckets_by_prompt_version[prompt_key].add(row, config)

  metrics_by_model_name = {
    k: acc.get_metrics() for k, acc in buckets_by_model_name.items()
  }
  metrics_by_prompt_version = {
    k: acc.get_metrics() for k, acc in buckets_by_prompt_version.items()
  }

  return MetricsJson(
    meta=config.to_meta(),
    overall=overall_bucket.get_metrics(),
    by_model_name=metrics_by_model_name,
    by_prompt_version=metrics_by_prompt_version,
    curves=build_curves_placeholder(),
  )
