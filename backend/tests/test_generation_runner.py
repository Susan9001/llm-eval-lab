# backend/tests/test_generation_runner.py
from __future__ import annotations

from time import sleep


from app.generation.generation_runner import run_one_generation, run_generation
from app.generation.generation_types import (
  GenerationRequest,
  GenerationResponse,
  Usage,
)
from app.generation.adapters.base import GenerationAdapter


def _make_rendered_prompt(*, source_sample_id: str = "s1") -> dict:
  return {
    "dataset_group_uid": "truthfulqa",
    "dataset_version": "v_test",
    "split": "test",
    "source_sample_id": source_sample_id,
    "prompt_group_uid": "truthfulqa_generation_base",
    "prompt_version": "v1",
    "prompt_path": "prompts/truthfulqa_generation_base/v1.txt",
    "rendered_prompt": "Say hi",
  }


class FastOkAdapter:
  def generate(self, req: GenerationRequest) -> GenerationResponse:
    # 给一点点延迟，避免 latency_ms 被 int 截断成 0 的偶发情况
    sleep(0.01)
    usage: Usage = {
      "prompt_tokens": None,
      "completion_tokens": None,
      "total_tokens": None,
      "provider_request_id": None,
      "finish_reason": None,
      "cost_usd": None,
    }
    return {
      "output_text": "ok",
      "generation_status": "SUCCESS",
      "generation_error_message": None,
      "usage_json": usage,
    }


class BoomAdapter:
  def generate(self, req: GenerationRequest) -> GenerationResponse:
    raise RuntimeError("boom")


def test_run_one_generation_success():
  rp = _make_rendered_prompt()
  adapter: GenerationAdapter = FastOkAdapter()

  out = run_one_generation(
    adapter,
    rp,
    provider="mock",
    model_name="mock-model",
    generation_params={"temperature": 0.0},
  )

  assert out["generation_status"] == "SUCCESS"
  assert out["output_text"] == "ok"
  assert out["generation_error_message"] is None

  # timestamps
  assert isinstance(out["started_at"], str)
  assert isinstance(out["finished_at"], str)
  assert out["started_at"].endswith("Z")
  assert out["finished_at"].endswith("Z")

  # latency
  assert isinstance(out["latency_ms"], int)
  assert out["latency_ms"] >= 0

  # identity fields
  assert out["dataset_group_uid"] == "truthfulqa"
  assert out["prompt_group_uid"] == "truthfulqa_generation_base"
  assert out["source_sample_id"] == "s1"


def test_run_one_generation_error():
  rp = _make_rendered_prompt()
  adapter: GenerationAdapter = BoomAdapter()

  out = run_one_generation(
    adapter,
    rp,
    provider="mock",
    model_name="mock-model",
    generation_params=None,
  )

  assert out["generation_status"] == "ERROR"
  assert out["output_text"] is None
  assert out["generation_error_message"] is not None
  assert "boom" in out["generation_error_message"]

  # still filled
  assert out["usage_json"]["prompt_tokens"] is None
  assert isinstance(out["latency_ms"], int)
  assert out["latency_ms"] >= 0


def test_run_generation_batch_len_and_order():
  adapter: GenerationAdapter = FastOkAdapter()
  prompts = [
    _make_rendered_prompt(source_sample_id="a"),
    _make_rendered_prompt(source_sample_id="b"),
    _make_rendered_prompt(source_sample_id="c"),
  ]

  outs = run_generation(
    prompts,
    provider="mock",
    model_name="mock-model",
    generation_params=None,
    adapter=adapter,
  )

  assert [o["source_sample_id"] for o in outs] == ["a", "b", "c"]
  assert all(o["generation_status"] == "SUCCESS" for o in outs)
