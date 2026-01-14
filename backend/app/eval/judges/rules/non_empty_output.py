from app.eval.eval_types import EvalRequest, RuleOutcome
from app.eval.statuses import RULE_STATUS_SUCCEEDED


class NonEmptyOutputRule:
  """
  A rule that checks if the model output is non-empty.
  """

  name = "non_empty_output"

  def apply(self, req: EvalRequest) -> RuleOutcome:
    output_text = req.get("output_text")

    if not output_text or not output_text.strip():
      return {
        "status": RULE_STATUS_SUCCEEDED,
        "score": 0.0,
        "rationale": "Output is empty or whitespace-only",
        "error_message": None,
      }

    return {
      "status": RULE_STATUS_SUCCEEDED,
      "score": 1.0,
      "rationale": f"Output is non-empty ({len(output_text.strip())} chars)",
      "error_message": None,
    }
