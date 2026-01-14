from collections.abc import Callable
from typing import Protocol

from app.eval.eval_types import EvalRequest, EvalResultRow, JudgeType


class JudgeAdapter(Protocol):
  def evaluate(self, req: EvalRequest) -> EvalResultRow: ...


JudgeAdapterBuilder = Callable[..., JudgeAdapter]

ADAPTER_REGISTRY: dict[JudgeType, JudgeAdapterBuilder] = {}


def register_adapter(
  judge_type: JudgeType, builder: JudgeAdapterBuilder
) -> None:
  ADAPTER_REGISTRY[judge_type] = builder


def build_judge_adapter(judge_type: JudgeType, **kwargs) -> JudgeAdapter:
  if judge_type not in ADAPTER_REGISTRY:
    known = ", ".join(sorted(ADAPTER_REGISTRY.keys()))
    raise ValueError(f"Unknown judge_type '{judge_type}'. Known: {known}")
  return ADAPTER_REGISTRY[judge_type](**kwargs)
