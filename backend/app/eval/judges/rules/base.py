from typing import Protocol

from app.eval.eval_types import EvalRequest, RuleOutcome


class Rule(Protocol):
  """
  A small, composable scoring rule.
  """

  name: str

  def apply(self, req: EvalRequest) -> RuleOutcome: ...
