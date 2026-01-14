from typing import Protocol

from app.eval.eval_types import EvalRequest, RuleOutcome


class Rule(Protocol):
    name: str

    def apply(self, req: EvalRequest) -> RuleOutcome: ...


RULE_REGISTRY: dict[str, Rule] = {}


def register_rule(rule_name: str, rule: Rule) -> None:
    RULE_REGISTRY[rule_name] = rule


def get_rule(rule_name: str) -> Rule:
    if rule_name not in RULE_REGISTRY:
        known = ", ".join(sorted(RULE_REGISTRY.keys()))
        raise ValueError(f"Unknown rule_name '{rule_name}'. Known: {known}")
    return RULE_REGISTRY[rule_name]


def build_rules(rule_names: list[str]) -> list[Rule]:
    rules: list[Rule] = []
    for rule_name in rule_names:
        rules.append(get_rule(rule_name))
    return rules
