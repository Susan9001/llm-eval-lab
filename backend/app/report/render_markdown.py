from __future__ import annotations

import json
from typing import Any

from app.eval.aggregators.metrics.metrics_types import MetricsJson
from app.report.report_types import RunInfoSection, TopSamplesSection


def _format_number(value: object, digits: int = 6) -> str:
  if isinstance(value, bool) or value is None:
    return str(value)

  if isinstance(value, int):
    return str(value)

  if isinstance(value, float):
    text = f"{value:.{digits}f}"
    text = text.rstrip("0").rstrip(".")
    return text if text else "0"

  return str(value)


def _format_inline_json(value: object) -> str:
  try:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
  except Exception:
    return str(value)


def _format_text_cell(text: object) -> str:
  if text is None:
    return ""
  if not isinstance(text, str):
    text = str(text)

  text = text.replace("\n", " ").replace("\r", " ").strip()
  text = text.replace("|", "\\|")
  return text


def _render_kv_table(rows: list[tuple[str, object]]) -> str:
  lines = []
  lines.append("| Key | Value |")
  lines.append("| --- | --- |")
  for key, value in rows:
    value_text = _format_text_cell(_format_inline_json(value))
    lines.append(f"| `{key}` | {value_text} |")
  return "\n".join(lines)


def _render_run_info_section(run_info_section: RunInfoSection) -> str:
  keys = [
    "dataset_group_uid",
    "dataset_version",
    "split",
    "adapter_name",
    "dataset_display_name",
    "input_path",
    "file_format",
    "num_samples",
    "sampling",
    "created_at",
    "prompt_group_uid",
    "prompt_version",
    "provider",
    "model_name",
    "judge_type",
    "judge_name",
    "judge_version",
  ]

  rows: list[tuple[str, object]] = []
  for key in keys:
    if key in run_info_section:
      rows.append((key, run_info_section.get(key)))

  for key in sorted(run_info_section.keys()):
    if key in keys:
      continue
    rows.append((key, run_info_section.get(key)))

  return _render_kv_table(rows)


def _render_metrics_json(metrics_json: MetricsJson) -> str:
  """
  Show everything in MetricsJson except:
  - summary.by_model_name
  - summary.by_prompt_version
  - curves.by_model_name
  - curves.by_prompt_version
  """
  parts: list[str] = []

  meta = metrics_json.get("meta", {})
  parts.append("### Metrics Meta")
  parts.append(
    _render_kv_table([(key, meta.get(key)) for key in sorted(meta.keys())])
  )
  parts.append("")

  summary = metrics_json.get("summary", {})
  overall = summary.get("overall")
  parts.append("### Metrics Summary Overall")
  if isinstance(overall, dict):
    parts.append(
      _render_kv_table(
        [(key, overall.get(key)) for key in sorted(overall.keys())]
      )
    )
  else:
    parts.append("_Missing `summary.overall`._")
  parts.append("")

  curves = metrics_json.get("curves")
  parts.append("### Curves Overall")
  if not curves:
    parts.append("_Curves is null._")
    return "\n".join(parts)

  curves_overall = None
  try:
    curves_overall = curves.get("overall")
  except Exception:
    curves_overall = None

  if not isinstance(curves_overall, dict):
    parts.append("_Missing `curves.overall`._")
    return "\n".join(parts)

  scalar_keys = [
    "roc_auc",
    "pr_auc",
    "num_labeled",
    "num_labeled_pos",
    "num_labeled_neg",
  ]
  scalar_rows = [
    (key, curves_overall.get(key))
    for key in scalar_keys
    if key in curves_overall
  ]
  if scalar_rows:
    parts.append(_render_kv_table(scalar_rows))
    parts.append("")

  def render_curve_bundle(bundle_name: str) -> str:
    bundle = curves_overall.get(bundle_name)
    if not isinstance(bundle, dict):
      return f"- `{bundle_name}`: _missing_"

    def preview(values: object) -> str:
      if not isinstance(values, list):
        return _format_inline_json(values)
      n = len(values)
      head = values[:3]
      tail = values[-3:] if n > 3 else []
      return f"len={n}, head={head}, tail={tail}"

    rows = []
    for key in ["fprs", "tprs", "thresholds", "precisions", "recalls"]:
      if key in bundle:
        rows.append(f"  - `{key}`: {preview(bundle.get(key))}")
    if not rows:
      return f"- `{bundle_name}`: _empty_"
    return "\n".join([f"- `{bundle_name}`:"] + rows)

  roc = curves_overall.get("roc")
  pr = curves_overall.get("pr")

  if roc is not None:
    parts.append(render_curve_bundle("roc"))
    parts.append("")
  if pr is not None:
    parts.append(render_curve_bundle("pr"))
    parts.append("")

  return "\n".join(parts).rstrip()


def _render_top_samples_section(top_samples_section: TopSamplesSection) -> str:
  def render_list(title: str, items: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append(f"### {title}")
    lines.append("")
    lines.append("| source_sample_id | score | rationale |")
    lines.append("| --- | --- | --- |")

    if not items:
      lines.append("|  |  |  |")
      return "\n".join(lines)

    for item in items:
      source_sample_id = _format_text_cell(item.get("source_sample_id"))
      score_text = _format_number(item.get("score"))
      rationale_text = _format_text_cell(item.get("rationale"))
      lines.append(
        f"| `{source_sample_id}` | {score_text} | {rationale_text} |"
      )

    return "\n".join(lines)

  k_low = int(top_samples_section.get("k_low", 0))
  k_high = int(top_samples_section.get("k_high", 0))
  k_near = int(top_samples_section.get("k_near", 0))

  top_low_score = top_samples_section.get("top_low_score", [])
  top_high_score = top_samples_section.get("top_high_score", [])
  near_threshold = top_samples_section.get("near_threshold", [])

  parts = []
  parts.append("### Top Samples Config")
  parts.append(
    _render_kv_table([("k_low", k_low), ("k_high", k_high), ("k_near", k_near)])
  )
  parts.append("")

  parts.append(render_list("Top Low Score", list(top_low_score)))
  parts.append("")
  parts.append(render_list("Top High Score", list(top_high_score)))
  parts.append("")
  parts.append(render_list("Near Threshold", list(near_threshold)))
  parts.append("")

  return "\n".join(parts).rstrip()


def build_report_markdown(
  run_info_section: RunInfoSection,
  metrics_json: MetricsJson,
  top_samples_section: TopSamplesSection,
  title: str | None = None,
) -> str:
  """
  Produce markdown report content.

  Inputs are already prepared by CLI + extract.py:
  - run_info_section: built from snapshot_meta + first_eval_result_row
  - metrics_json: loaded from metrics json file
  - top_samples_section: built from eval_results.jsonl using primary_score_rule + threshold from metrics_json.meta
  """
  report_title = title or "LLM Eval Report"

  parts: list[str] = []
  parts.append(f"# {report_title}")
  parts.append("")
  parts.append("## Run Info")
  parts.append(_render_run_info_section(run_info_section))
  parts.append("")
  parts.append("## Metrics")
  parts.append(_render_metrics_json(metrics_json))
  parts.append("")
  parts.append("## Top Samples")
  parts.append(_render_top_samples_section(top_samples_section))
  parts.append("")

  return "\n".join(parts)
