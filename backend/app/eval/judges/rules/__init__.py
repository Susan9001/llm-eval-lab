from app.eval.judges.rules.base import register_rule
from app.eval.judges.rules.exact_match_reference import ExactMatchReferenceRule
from app.eval.judges.rules.non_empty_output import NonEmptyOutputRule

register_rule("exact_match_reference", ExactMatchReferenceRule())
register_rule("non_empty_output", NonEmptyOutputRule())
