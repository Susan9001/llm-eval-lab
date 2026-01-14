from app.eval.eval_types import EvalRequest, EvalResultRow


class LLMAdapter:
  """
  LLM as judege.
  """

  def evaluate(self, req: EvalRequest) -> EvalResultRow: ...
