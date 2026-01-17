from __future__ import annotations

from typing import NotRequired, TypedDict

from app.datasets.dataset_types import DatasetSnapshotMeta
from app.eval.eval_types import JudgeType
from app.prompts.prompt_types import PromptIdentifier


class RunInfoSection(DatasetSnapshotMeta, PromptIdentifier):
  provider: str
  model_name: str

  judge_type: JudgeType
  judge_name: str
  judge_version: NotRequired[str | None]


class SampleScoreItem(TypedDict, total=False):
  source_sample_id: str
  score: float
  rationale: str | None


class TopSamplesSection(TypedDict, total=False):
  k_low: int
  k_high: int
  k_near: int

  top_low_score: list[SampleScoreItem]
  top_high_score: list[SampleScoreItem]
  near_threshold: list[SampleScoreItem]
