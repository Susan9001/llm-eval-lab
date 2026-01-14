from __future__ import annotations

import pytest

from app.eval import eval_runner
from app.eval.statuses import EVAL_STATUS_FAILED


class DummyAdapter:
  def __init__(
    self,
    returned_row: dict | None = None,
    *,
    raise_exc: Exception | None = None,
  ) -> None:
    self._returned_row = returned_row or {}
    self._raise_exc = raise_exc

  def evaluate(self, req: dict) -> dict:
    if self._raise_exc is not None:
      raise self._raise_exc
    # Return a copy so runner mutations do not affect internal state.
    return dict(self._returned_row)


def make_rendered_prompt(
  *,
  dataset_group_uid: str = "dg",
  dataset_version: str = "v1",
  split: str = "test",
  source_sample_id: str = "s1",
  prompt_group_uid: str = "pg",
  prompt_version: str = "p1",
  prompt_path: str | None = "rp.jsonl",
  input_text: str | None = "hello",
  reference_output: str | None = "world",
) -> dict:
  rp = {
    "dataset_group_uid": dataset_group_uid,
    "dataset_version": dataset_version,
    "split": split,
    "source_sample_id": source_sample_id,
    "prompt_group_uid": prompt_group_uid,
    "prompt_version": prompt_version,
    "prompt_path": prompt_path,
    "input_text": input_text,
    "rendered_prompt": "Rendered prompt body",
  }
  if reference_output is not None:
    rp["reference_output"] = reference_output
  return rp


def make_model_output_row(
  *,
  dataset_group_uid: str = "dg",
  dataset_version: str = "v1",
  split: str = "test",
  source_sample_id: str = "s1",
  prompt_group_uid: str = "pg",
  prompt_version: str = "p1",
  prompt_path: str | None = "mo.jsonl",
  model_output_uuid: str = "uuid-1",
  provider: str = "mock",
  model_name: str = "mock-001",
  generation_params: dict | None = None,
  generation_status: str = "SUCCEEDED",
  generation_error_message: str | None = None,
  output_text: str | None = "out",
) -> dict:
  return {
    "dataset_group_uid": dataset_group_uid,
    "dataset_version": dataset_version,
    "split": split,
    "source_sample_id": source_sample_id,
    "prompt_group_uid": prompt_group_uid,
    "prompt_version": prompt_version,
    "prompt_path": prompt_path,
    "model_output_uuid": model_output_uuid,
    "provider": provider,
    "model_name": model_name,
    "generation_params": generation_params,
    "generation_status": generation_status,
    "generation_error_message": generation_error_message,
    "output_text": output_text,
  }


def test_index_rendered_prompts_duplicate_key_raises() -> None:
  rp1 = make_rendered_prompt(prompt_path="a.jsonl")
  rp2 = make_rendered_prompt(
    prompt_path="b.jsonl"
  )  # same identifier fields, different path

  with pytest.raises(ValueError) as exc_info:
    eval_runner.index_rendered_prompts([rp1, rp2])

  msg = str(exc_info.value)
  assert "Duplicate rendered prompt key detected" in msg
  assert "existing_prompt_path=a.jsonl" in msg
  assert "new_prompt_path=b.jsonl" in msg


def test_build_eval_request_prompt_path_preference() -> None:
  rp = make_rendered_prompt(prompt_path="rp.jsonl")

  mo_has_path = make_model_output_row(prompt_path="mo.jsonl")
  req1 = eval_runner.build_eval_request(rp, mo_has_path)
  assert req1["prompt_path"] == "mo.jsonl"

  mo_no_path = make_model_output_row(prompt_path=None)
  req2 = eval_runner.build_eval_request(rp, mo_no_path)
  assert req2["prompt_path"] == "rp.jsonl"


def test_iter_eval_results_missing_rendered_prompt_includes_model_info(
  monkeypatch,
) -> None:
  # Prevent registry / builder behavior from affecting this unit test.
  monkeypatch.setattr(
    eval_runner,
    "build_judge_adapter",
    lambda judge_type, **kwargs: DummyAdapter(),
  )

  mo = make_model_output_row(
    model_output_uuid="uuid-miss",
    provider="openai",
    model_name="gpt-x",
  )

  with pytest.raises(ValueError) as exc_info:
    list(
      eval_runner.iter_eval_results(
        rendered_prompts=[],
        model_output_rows=[mo],
        judge_type="rule",
        judge_name="rule_judge",
      )
    )

  msg = str(exc_info.value)
  assert "Missing rendered prompt for model output row" in msg
  assert "model_output_uuid=uuid-miss" in msg
  assert "provider=openai" in msg
  assert "model_name=gpt-x" in msg
  assert "rendered_prompt_key=" in msg


def test_run_one_eval_overwrites_identity_and_timing_fields() -> None:
  rp = make_rendered_prompt()
  mo = make_model_output_row(
    model_output_uuid="uuid-2", provider="p1", model_name="m1"
  )

  adapter = DummyAdapter(
    returned_row={
      # Intentionally wrong values, runner should overwrite these.
      "dataset_group_uid": "WRONG",
      "provider": "WRONG",
      "model_name": "WRONG",
      "judge_type": "WRONG",
      "judge_name": "WRONG",
      "judge_version": "WRONG",
      "started_at": "WRONG",
      "finished_at": "WRONG",
      "latency_ms": -123,
      # Minimal fields that a judge typically returns.
      "eval_status": "SUCCEEDED",
      "eval_error_message": None,
      "rule_outcomes": {},
      "generation_status": "SUCCEEDED",
      "generation_error_message": None,
    }
  )

  res = eval_runner.run_one_eval(
    adapter,
    rp,
    mo,
    judge_type="rule",
    judge_name="rule_judge",
    judge_version="v0",
  )

  assert res["dataset_group_uid"] == rp["dataset_group_uid"]
  assert res["dataset_version"] == rp["dataset_version"]
  assert res["split"] == rp["split"]
  assert res["source_sample_id"] == rp["source_sample_id"]
  assert res["prompt_group_uid"] == rp["prompt_group_uid"]
  assert res["prompt_version"] == rp["prompt_version"]

  assert res["model_output_uuid"] == mo["model_output_uuid"]
  assert res["provider"] == mo["provider"]
  assert res["model_name"] == mo["model_name"]

  assert res["judge_type"] == "rule"
  assert res["judge_name"] == "rule_judge"
  assert res["judge_version"] == "v0"

  assert res["started_at"] != "WRONG"
  assert res["finished_at"] != "WRONG"
  assert isinstance(res["latency_ms"], int)
  assert res["latency_ms"] >= 0


def test_run_one_eval_adapter_exception_builds_failed_result() -> None:
  rp = make_rendered_prompt()
  mo = make_model_output_row(
    model_output_uuid="uuid-err", provider="p2", model_name="m2"
  )

  adapter = DummyAdapter(raise_exc=RuntimeError("boom"))

  res = eval_runner.run_one_eval(
    adapter,
    rp,
    mo,
    judge_type="rule",
    judge_name="rule_judge",
    judge_version=None,
  )

  assert res["eval_status"] == EVAL_STATUS_FAILED
  assert res["eval_error_message"] is not None
  assert "RuntimeError" in res["eval_error_message"]
  assert "boom" in res["eval_error_message"]
  assert isinstance(res["latency_ms"], int)
  assert res["latency_ms"] >= 0
