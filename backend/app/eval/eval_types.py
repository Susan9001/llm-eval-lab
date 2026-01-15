from __future__ import annotations

from typing import Literal, TypedDict

from app.prompts.prompt_types import RenderedPromptIdentifier

JudgeType = Literal["rule", "llm"]

JUDGE_TYPE_RULE: JudgeType = "rule"
JUDGE_TYPE_LLM: JudgeType = "llm"


class EvalRequest(RenderedPromptIdentifier):
  """
  A single unit of evaluation.

  Built by joining:
    RenderedPrompt (input_text, reference_output, prompt identity)
    ModelOutputRow (model_output_uuid)
  """

  model_output_uuid: str

  provider: str
  model_name: str
  generation_params: dict[str, object] | None

  generation_status: str
  generation_error_message: str | None

  input_text: str | None
  reference_output: str | None
  output_text: str | None

  # For LLM-as-judge only.
  rendered_eval_prompt: str | None
  # Optional, for supervised eval or curves. value should be 0 or 1 only.
  # Example: {"harmful": 0} or {"harmful": 1}
  labels: dict[str, object] | None


class RuleOutcome(TypedDict):
  """
  Output of a single rule.

  score:
    Prefer 0.0 to 1.0.
    Use None when SKIPPED or ERROR.
  """

  status: str
  score: float | None
  rationale: str | None
  error_message: str | None


class EvalResultRow(RenderedPromptIdentifier):
  """
  One row to write into eval_results.jsonl.
  """

  model_output_uuid: str

  provider: str
  model_name: str

  # Generation status from ModelOutputRow
  generation_status: str
  generation_error_message: str | None

  judge_type: JudgeType
  judge_name: str
  judge_version: str | None

  eval_status: str
  eval_error_message: str | None

  # rule_name -> outcome
  rule_outcomes: dict[str, RuleOutcome]
  # Optional, for supervised eval or curves. value should be 0 or 1 only.
  # Example: {"harmful": 0} or {"harmful": 1}
  labels: dict[str, object] | None

  started_at: str
  finished_at: str
  latency_ms: int | None
