from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any

from app.report.extract import build_run_info_section, build_top_samples_section
from app.report.render_markdown import build_report_markdown
from app.utils.file_io import iter_rows_from_jsonl, read_json


@dataclass(frozen=True)
class ReportMarkdownCliArgs:
  snapshot_meta_path: str
  metrics_path: str
  eval_results_path: str
  report_path: str

  title: str | None
  k_low: int
  k_high: int
  k_near: int
  rationale_max_len: int


def _require_nonnegative_int(value: str) -> int:
  try:
    int_value = int(value)
  except Exception as exc:
    raise argparse.ArgumentTypeError(f"Expected int, got {value}") from exc

  if int_value < 0:
    raise argparse.ArgumentTypeError(
      f"Expected non-negative int, got {int_value}"
    )

  return int_value


def _extract_primary_score_rule(metrics_json: dict[str, Any]) -> str:
  meta = metrics_json.get("meta", {})
  primary_score_rule = meta.get("primary_score_rule")
  if not isinstance(primary_score_rule, str) or not primary_score_rule:
    raise ValueError(
      "metrics_json.meta.primary_score_rule must be a non-empty str"
    )
  return primary_score_rule


def _extract_threshold(metrics_json: dict[str, Any]) -> float | None:
  meta = metrics_json.get("meta", {})
  threshold = meta.get("threshold")
  if threshold is None:
    return None
  try:
    return float(threshold)
  except Exception:
    return None


def parse_args() -> ReportMarkdownCliArgs:
  parser = argparse.ArgumentParser(
    prog="report_markdown_cli",
    description="Generate a markdown report from eval artifacts.",
  )

  parser.add_argument("--snapshot-meta-path", required=True)
  parser.add_argument("--metrics-path", required=True)
  parser.add_argument("--eval-results-path", required=True)
  parser.add_argument("--report-path", required=True)

  parser.add_argument("--title", default=None)

  parser.add_argument("--k-low", type=_require_nonnegative_int, default=10)
  parser.add_argument("--k-high", type=_require_nonnegative_int, default=10)
  parser.add_argument("--k-near", type=_require_nonnegative_int, default=10)
  parser.add_argument(
    "--rationale-max-len", type=_require_nonnegative_int, default=120
  )

  args = parser.parse_args()

  return ReportMarkdownCliArgs(
    snapshot_meta_path=args.snapshot_meta_path,
    metrics_path=args.metrics_path,
    eval_results_path=args.eval_results_path,
    report_path=args.report_path,
    title=args.title,
    k_low=args.k_low,
    k_high=args.k_high,
    k_near=args.k_near,
    rationale_max_len=args.rationale_max_len,
  )


def generate_markdown_report(args: ReportMarkdownCliArgs) -> None:
  snapshot_meta = read_json(args.snapshot_meta_path)
  metrics_json = read_json(args.metrics_path)

  primary_score_rule = _extract_primary_score_rule(metrics_json)
  threshold = _extract_threshold(metrics_json)

  eval_result_rows = list(
    iter_rows_from_jsonl(
      args.eval_results_path,
      required_keys=[
        "source_sample_id",
        "prompt_group_uid",
        "prompt_version",
        "provider",
        "model_name",
        "judge_type",
        "judge_name",
        "rule_outcomes",
      ],
    )
  )
  if not eval_result_rows:
    raise ValueError(f"Empty eval results: {args.eval_results_path}")

  run_info_section = build_run_info_section(
    snapshot_meta=snapshot_meta,
    first_eval_result_row=eval_result_rows[0],
  )

  top_samples_section = build_top_samples_section(
    eval_result_rows=eval_result_rows,
    primary_score_rule=primary_score_rule,
    threshold=threshold,
    k_low=args.k_low,
    k_high=args.k_high,
    k_near=args.k_near,
    rationale_max_len=args.rationale_max_len,
  )

  markdown = build_report_markdown(
    run_info_section=run_info_section,
    metrics_json=metrics_json,
    top_samples_section=top_samples_section,
    title=args.title,
  )

  with open(args.report_path, "w", encoding="utf-8") as file:
    file.write(markdown)


if __name__ == "__main__":
  generate_markdown_report(parse_args())
