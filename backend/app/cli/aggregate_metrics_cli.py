from __future__ import annotations

import argparse
import json
from dataclasses import dataclass

from app.eval.aggregators.metrics.aggregate_metrics import build_metrics
from app.eval.aggregators.metrics.metrics_types import MetricsBuildConfig
from app.utils.file_io import ensure_parent_dir, iter_rows_from_jsonl
from app.utils.time_utils import utc_now_iso8601


eval_results_required_keys = [
  "model_name",
  "prompt_group_uid",
  "prompt_version",
  "generation_status",
  "eval_status",
  "rule_outcomes",
]


@dataclass(frozen=True)
class MetricsCliArgs:
  eval_results_path: str
  metrics_path: str
  primary_score_rule: str
  threshold: float


def parse_args() -> MetricsCliArgs:
  parser = argparse.ArgumentParser(
    description="Aggregate eval_results.jsonl into metrics.json.",
  )

  parser.add_argument(
    "--eval-results-path",
    required=True,
    help="Path to eval_results.jsonl.",
  )
  parser.add_argument(
    "--metrics-path",
    required=True,
    help="Output path for metrics.json.",
  )
  parser.add_argument(
    "--primary-score-rule",
    required=True,
    help="Rule name used as the primary score source in rule_outcomes.",
  )
  parser.add_argument(
    "--threshold",
    required=True,
    type=float,
    help="Threshold for over_threshold_rate, pass if score >= threshold.",
  )

  ns = parser.parse_args()

  return MetricsCliArgs(
    eval_results_path=ns.eval_results_path,
    metrics_path=ns.metrics_path,
    primary_score_rule=ns.primary_score_rule,
    threshold=ns.threshold,
  )


def run_metrics(args: MetricsCliArgs) -> None:
  eval_results_rows = iter_rows_from_jsonl(
    args.eval_results_path,
    required_keys=eval_results_required_keys,
  )

  config = MetricsBuildConfig(
    generated_at=utc_now_iso8601(),
    threshold=args.threshold,
    primary_score_rule=args.primary_score_rule,
  )

  metrics = build_metrics(
    eval_results_rows=eval_results_rows,
    config=config,
  )

  ensure_parent_dir(args.metrics_path)
  with open(args.metrics_path, "w", encoding="utf-8") as f:
    json.dump(metrics, f, ensure_ascii=False, indent=2)

  print(f"Wrote metrics to {args.metrics_path}")


if __name__ == "__main__":
  run_metrics(parse_args())
