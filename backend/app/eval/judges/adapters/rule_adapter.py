from __future__ import annotations

from app.eval.eval_types import (
  EvalRequest,
  EvalResultRow,
  RuleOutcome,
  JUDGE_TYPE_RULE,
)
from app.eval.judges.rules.base import build_rules
from app.eval.statuses import (
  EVAL_STATUS_FAILED,
  EVAL_STATUS_SUCCEEDED,
  RULE_STATUS_FAILED,
)
from app.generation.statuses import GENERATION_STATUS_SUCCEEDED


class RuleAdapter:
  """
  Judge model output by rules.
  """

  def __init__(
    self,
    *,
    rule_names: list[str],
    judge_name: str = "rule_judge",
    judge_version: str | None = None,
  ) -> None:
    if not rule_names:
      raise ValueError("rule_names must be a non-empty list.")

    self._rule_names = rule_names
    self._judge_name = judge_name
    self._judge_version = judge_version

  def evaluate(self, req: EvalRequest) -> EvalResultRow:
    eval_status: str
    eval_error_message: str | None = None
    rule_outcomes: dict[str, RuleOutcome] = {}

    try:
      generation_status = req["generation_status"]
      if generation_status != GENERATION_STATUS_SUCCEEDED:
        eval_status = EVAL_STATUS_FAILED
        eval_error_message = (
          f"generation_status={generation_status}, "
          f"generation_error_message={req.get('generation_error_message')}"
        )
      else:
        rules = build_rules(self._rule_names)

        for rule in rules:
          try:
            rule_outcomes[rule.name] = rule.apply(req)
          except Exception as e:
            rule_outcomes[rule.name] = RuleOutcome(
              status=RULE_STATUS_FAILED,
              score=None,
              rationale=None,
              error_message=f"{type(e).__name__}: {e}",
            )

        if any(
          outcome.get("status") == RULE_STATUS_FAILED
          for outcome in rule_outcomes.values()
        ):
          eval_status = EVAL_STATUS_FAILED
          eval_error_message = "One or more rules failed."
        else:
          eval_status = EVAL_STATUS_SUCCEEDED

    except Exception as e:
      eval_status = EVAL_STATUS_FAILED
      eval_error_message = str(e)

    res: EvalResultRow = EvalResultRow(
      # RenderedPromptIdentifier fields (inherited)
      dataset_group_uid=req["dataset_group_uid"],
      dataset_version=req["dataset_version"],
      split=req["split"],
      source_sample_id=req["source_sample_id"],
      prompt_group_uid=req["prompt_group_uid"],
      prompt_version=req["prompt_version"],
      prompt_path=req.get("prompt_path"),
      # Trace to one concrete output
      model_output_uuid=req["model_output_uuid"],
      # Model identity
      provider=req["provider"],
      model_name=req["model_name"],
      # Generation status
      generation_status=req["generation_status"],
      generation_error_message=req.get("generation_error_message"),
      # Judge identity
      judge_type=JUDGE_TYPE_RULE,
      judge_name=self._judge_name,
      judge_version=self._judge_version,
      # Status
      eval_status=eval_status,
      eval_error_message=eval_error_message,
      # Rule results
      rule_outcomes=rule_outcomes,
    )
    return res
