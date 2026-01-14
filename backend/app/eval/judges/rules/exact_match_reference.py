from app.common.statuses import RULE_STATUS_SKIPPED, RULE_STATUS_SUCCEEDED
from app.eval.eval_types import EvalRequest, RuleOutcome


class ExactMatchReferenceRule:
  """
  A rule that checks if the model output exactly matches the reference output.
  """

  name = "exact_match_reference"

  def _normalize(self, text: str) -> str:
    """Simple normalization: strip whitespace and lowercase."""
    return text.strip().lower()

  def apply(self, req: EvalRequest) -> RuleOutcome:
    reference_output = req.get("reference_output")
    output_text = req.get("output_text")

    # Skip if reference is missing
    if reference_output is None:
      return RuleOutcome(
        status=RULE_STATUS_SKIPPED,
        score=None,
        rationale="Reference output is missing",
        error_message=None,
      )

    # Skip if model output is missing
    if output_text is None:
      return RuleOutcome(
        status=RULE_STATUS_SKIPPED,
        score=None,
        rationale="Model output is missing",
        error_message=None,
      )

    # Compare after normalization
    normalized_ref = self._normalize(reference_output)
    normalized_output = self._normalize(output_text)
    matches = normalized_ref == normalized_output

    if matches:
      return RuleOutcome(
        status=RULE_STATUS_SUCCEEDED,
        score=1.0,
        rationale="Output matches reference after normalization",
        error_message=None,
      )
    else:
      return RuleOutcome(
        status=RULE_STATUS_SUCCEEDED,
        score=0.0,
        rationale="Output does not match reference after normalization.",
        error_message=None,
      )
