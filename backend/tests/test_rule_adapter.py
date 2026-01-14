import pytest

from app.common.statuses import (
  EVAL_STATUS_FAILED,
  EVAL_STATUS_SUCCEEDED,
  GENERATION_STATUS_SUCCEEDED,
  RULE_STATUS_FAILED,
  RULE_STATUS_SUCCEEDED,
)
from app.eval.judges.adapters.rule_adapter import RuleAdapter


class _FakeRule:
  def __init__(self, name: str, apply_fn):
    self.name = name
    self._apply_fn = apply_fn

  def apply(self, req):
    return self._apply_fn(req)


def _make_req(*, generation_status: str):
  return {
    "dataset_group_uid": "ds_group",
    "dataset_version": "v1",
    "split": "test",
    "source_sample_id": "s1",
    "prompt_group_uid": "pg",
    "prompt_version": "p1",
    "prompt_path": None,
    "model_output_uuid": "uuid-1",
    "provider": "mock",
    "model_name": "mock-1",
    "generation_status": generation_status,
    "generation_error_message": "gen failed",
    # 下面这些不是 RuleAdapter 必用，但真实 rule 可能会用到。
    "input_text": "hi",
    "reference_output": "hello",
    "output_text": "hello",
    "rendered_eval_prompt": None,
  }


def test_init_rule_names_empty_raises():
  with pytest.raises(ValueError, match="rule_names must be a non-empty list"):
    RuleAdapter(rule_names=[])


def test_evaluate_generation_not_succeeded_marks_eval_failed(monkeypatch):
  monkeypatch.setattr(
    "app.eval.judges.adapters.rule_adapter.build_rules",
    lambda rule_names: [
      _FakeRule(
        "r1",
        lambda req: {
          "status": RULE_STATUS_SUCCEEDED,
          "score": 1.0,
          "rationale": None,
          "error_message": None,
        },
      )
    ],
  )

  adapter = RuleAdapter(rule_names=["r1"])
  req = _make_req(generation_status="FAILED")

  res = adapter.evaluate(req)

  assert res["eval_status"] == EVAL_STATUS_FAILED
  assert res["rule_outcomes"] == {}
  assert res["eval_error_message"] is not None
  assert "generation_status=" in res["eval_error_message"]
  # Generation status fields should be copied
  assert res["generation_status"] == "FAILED"
  assert res["generation_error_message"] == "gen failed"


def test_evaluate_all_rules_succeeded_eval_succeeded(monkeypatch):
  rules = [
    _FakeRule(
      "r_ok",
      lambda req: {
        "status": RULE_STATUS_SUCCEEDED,
        "score": 1.0,
        "rationale": "ok",
        "error_message": None,
      },
    )
  ]
  monkeypatch.setattr(
    "app.eval.judges.adapters.rule_adapter.build_rules",
    lambda rule_names: rules,
  )

  adapter = RuleAdapter(rule_names=["r_ok"])
  req = _make_req(generation_status=GENERATION_STATUS_SUCCEEDED)

  res = adapter.evaluate(req)

  assert res["eval_status"] == EVAL_STATUS_SUCCEEDED
  assert res["eval_error_message"] is None
  assert "r_ok" in res["rule_outcomes"]
  assert res["rule_outcomes"]["r_ok"]["status"] == RULE_STATUS_SUCCEEDED
  # Generation status fields should be copied
  assert res["generation_status"] == GENERATION_STATUS_SUCCEEDED
  assert res["generation_error_message"] == "gen failed"


def test_evaluate_one_rule_throws_marks_rule_failed_and_eval_failed(
  monkeypatch,
):
  def _raise(req):
    raise RuntimeError("boom")

  rules = [
    _FakeRule(
      "r_ok",
      lambda req: {
        "status": RULE_STATUS_SUCCEEDED,
        "score": 1.0,
        "rationale": None,
        "error_message": None,
      },
    ),
    _FakeRule("r_boom", _raise),
  ]
  monkeypatch.setattr(
    "app.eval.judges.adapters.rule_adapter.build_rules",
    lambda rule_names: rules,
  )

  adapter = RuleAdapter(rule_names=["r_ok", "r_boom"])
  req = _make_req(generation_status=GENERATION_STATUS_SUCCEEDED)

  res = adapter.evaluate(req)

  assert res["eval_status"] == EVAL_STATUS_FAILED
  assert res["eval_error_message"] == "One or more rules failed."

  assert res["rule_outcomes"]["r_ok"]["status"] == RULE_STATUS_SUCCEEDED
  assert res["rule_outcomes"]["r_boom"]["status"] == RULE_STATUS_FAILED
  assert "RuntimeError" in (
    res["rule_outcomes"]["r_boom"]["error_message"] or ""
  )
  # Generation status fields should be copied
  assert res["generation_status"] == GENERATION_STATUS_SUCCEEDED
  assert res["generation_error_message"] == "gen failed"
