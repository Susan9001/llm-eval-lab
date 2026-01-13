from typing import Protocol

from app.eval.eval_types import EvalRequest, EvalResultRow


class JudgeAdapter(Protocol):
  """
  Adapter abstraction, similar to generation adapters.

  RuleAdapter and LLMAdapter both implement this.
  """

  def evaluate(self, req: EvalRequest) -> EvalResultRow: ...
