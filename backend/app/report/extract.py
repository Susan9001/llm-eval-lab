from __future__ import annotations

import heapq
from collections.abc import Iterable

from app.common.statuses import RULE_STATUS_SUCCEEDED
from app.datasets.dataset_types import DatasetSnapshotMeta
from app.eval.eval_types import EvalResultRow
from app.report.report_types import (
  RunInfoSection,
  SampleScoreItem,
  TopSamplesSection,
)


def _truncate_text(text: str | None, max_len: int) -> str | None:
  if text is None:
    return None
  if max_len <= 0:
    return ""
  if len(text) <= max_len:
    return text
  return text[: max_len - 1] + "…"


def _get_primary_item(
  eval_result_row: EvalResultRow,
  primary_score_rule: str,
  rationale_max_len: int,
) -> SampleScoreItem | None:
  """
  Extract SampleScoreItem from one EvalResultRow using primary_score_rule.
  If anything is missing or malformed, return None.
  """
  try:
    outcome = eval_result_row["rule_outcomes"][primary_score_rule]
    if outcome["status"] != RULE_STATUS_SUCCEEDED:
      return None

    score = outcome["score"]
    if score is None:
      return None

    return {
      "source_sample_id": eval_result_row["source_sample_id"],
      "score": float(score),
      "rationale": _truncate_text(outcome.get("rationale"), rationale_max_len),
    }
  except Exception:
    return None


def build_run_info_section(
  snapshot_meta: DatasetSnapshotMeta,
  first_eval_result_row: EvalResultRow,
) -> RunInfoSection:
  """
  Build Section A (RunInfoSection).

  This intentionally does NOT include any MetricsJson.meta fields.
  """
  return {
    **snapshot_meta,
    "prompt_group_uid": first_eval_result_row["prompt_group_uid"],
    "prompt_version": first_eval_result_row["prompt_version"],
    "provider": first_eval_result_row["provider"],
    "model_name": first_eval_result_row["model_name"],
    "judge_type": first_eval_result_row["judge_type"],
    "judge_name": first_eval_result_row["judge_name"],
    "judge_version": first_eval_result_row.get("judge_version"),
  }


def build_top_samples_section(
  eval_result_rows: Iterable[EvalResultRow],
  primary_score_rule: str,
  threshold: float | None,
  k_low: int,
  k_high: int,
  k_near: int,
  rationale_max_len: int = 120,
) -> TopSamplesSection:
  """
  Build Section D (TopSamplesSection).

  Rules:
  - Each list has its own k.
  - If k == 0, the list is an empty list.
  - Near-threshold list is empty when threshold is None.
  - Returned section does NOT include primary_score_rule or threshold.
  """
  lowHeap: list[tuple[float, str, str | None]] = []
  highHeap: list[tuple[float, str, str | None]] = []
  nearHeap: list[tuple[float, float, str, str | None]] = []

  for eval_result_row in eval_result_rows:
    item = _get_primary_item(
      eval_result_row=eval_result_row,
      primary_score_rule=primary_score_rule,
      rationale_max_len=rationale_max_len,
    )
    if item is None:
      continue

    source_sample_id = item["source_sample_id"]
    score = item["score"]
    rationale = item.get("rationale")

    if k_low > 0:
      # Keep k_low smallest scores: pop the largest score when overflow.
      heapq.heappush(lowHeap, (-score, source_sample_id, rationale))
      if len(lowHeap) > k_low:
        heapq.heappop(lowHeap)

    if k_high > 0:
      # Keep k_high largest scores: pop the smallest score when overflow.
      heapq.heappush(highHeap, (score, source_sample_id, rationale))
      if len(highHeap) > k_high:
        heapq.heappop(highHeap)

    if threshold is not None and k_near > 0:
      # Keep k_near closest to threshold: pop the farthest when overflow.
      diff = abs(score - threshold)
      heapq.heappush(nearHeap, (-diff, score, source_sample_id, rationale))
      if len(nearHeap) > k_near:
        heapq.heappop(nearHeap)

  top_low_score = [
    {
      "source_sample_id": source_sample_id,
      "score": -neg_score,
      "rationale": rationale,
    }
    for (neg_score, source_sample_id, rationale) in lowHeap
  ]
  top_low_score.sort(key=lambda x: (x["score"], x["source_sample_id"]))

  top_high_score = [
    {
      "source_sample_id": source_sample_id,
      "score": score,
      "rationale": rationale,
    }
    for (score, source_sample_id, rationale) in highHeap
  ]
  top_high_score.sort(key=lambda x: (-x["score"], x["source_sample_id"]))

  near_threshold: list[SampleScoreItem] = []
  if threshold is not None:
    near_threshold = [
      {
        "source_sample_id": source_sample_id,
        "score": score,
        "rationale": rationale,
      }
      for (_neg_diff, score, source_sample_id, rationale) in nearHeap
    ]
    near_threshold.sort(
      key=lambda x: (abs(x["score"] - threshold), x["source_sample_id"])
    )

  return {
    "k_low": int(k_low),
    "k_high": int(k_high),
    "k_near": int(k_near),
    "top_low_score": top_low_score,
    "top_high_score": top_high_score,
    "near_threshold": near_threshold,
  }
