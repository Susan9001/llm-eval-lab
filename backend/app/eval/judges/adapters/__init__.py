from app.eval.judges.adapters.base import register_adapter
from app.eval.judges.adapters.rule_adapter import RuleAdapter
from app.eval.judges.adapters.llm_adapter import LLMAdapter
from app.eval.eval_types import JUDGE_TYPE_RULE, JUDGE_TYPE_LLM

register_adapter(JUDGE_TYPE_RULE, RuleAdapter)
register_adapter(JUDGE_TYPE_LLM, LLMAdapter)