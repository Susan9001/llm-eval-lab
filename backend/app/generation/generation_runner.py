from __future__ import annotations

from collections.abc import Iterable, Iterator
from time import perf_counter
import uuid

from app.common.statuses import GENERATION_STATUS_FAILED
from app.generation.adapters.base import (
  GenerationAdapter,
  get_gen_model_adapter,
)
from app.generation.generation_types import (
  GenerationRequest,
  GenerationResponse,
  ModelOutputRow,
  Usage,
)
from app.prompts.prompt_types import RenderedPrompt
from app.utils.time_utils import utc_now_iso8601


def _empty_usage() -> Usage:
  return Usage(
    prompt_tokens=None,
    completion_tokens=None,
    total_tokens=None,
    provider_request_id=None,
    finish_reason=None,
    cost_usd=None,
  )


def run_one_generation(
  adapter: GenerationAdapter,
  rp: RenderedPrompt,
  *,
  provider: str,
  model_name: str,
  generation_params: dict[str, object] | None,
) -> ModelOutputRow:
  """
  Run generation for one RenderedPrompt and return one ModelOutputRow row.
  """
  params = generation_params or {}

  started_at = utc_now_iso8601()
  start_perf = perf_counter()

  output_text: str | None
  generation_status: str
  generation_error_message: str | None
  usage_json: Usage

  try:
    req: GenerationRequest = GenerationRequest(
      rendered_prompt=rp["rendered_prompt"],
      provider=provider,
      model_name=model_name,
      generation_params=params,
    )

    resp: GenerationResponse = adapter.generate(req)

    output_text = resp["output_text"]
    generation_status = resp["generation_status"]
    generation_error_message = resp["generation_error_message"]
    usage_json = resp["usage_json"]
  except Exception as e:
    output_text = None
    generation_status = GENERATION_STATUS_FAILED
    generation_error_message = str(e)
    usage_json = _empty_usage()
  finally:
    finished_at = utc_now_iso8601()
    latency_ms = max(int((perf_counter() - start_perf) * 1000), 0)

  model_output_uuid = str(uuid.uuid4())

  return ModelOutputRow(
    model_output_uuid=model_output_uuid,
    # Dataset snapshot identifier (inherited)
    dataset_group_uid=rp["dataset_group_uid"],
    dataset_version=rp["dataset_version"],
    split=rp["split"],
    # Sample identifier
    source_sample_id=rp["source_sample_id"],
    # Prompt identity
    prompt_group_uid=rp["prompt_group_uid"],
    prompt_version=rp["prompt_version"],
    prompt_path=rp.get("prompt_path"),
    # Model invocation config
    provider=provider,
    model_name=model_name,
    generation_params=params,
    # Model results
    output_text=output_text,
    generation_status=generation_status,
    generation_error_message=generation_error_message,
    usage_json=usage_json,
    # Timing
    started_at=started_at,
    finished_at=finished_at,
    latency_ms=latency_ms,
  )


def iter_generation_outputs(
  rendered_prompts: Iterable[RenderedPrompt],
  *,
  provider: str,
  model_name: str,
  generation_params: dict[str, object] | None = None,
  adapter: GenerationAdapter | None = None,
) -> Iterator[ModelOutputRow]:
  """
  Yield ModelOutputRow rows one-by-one (streaming friendly).
  If adapter is None, we resolve it from registry via get_adapter(provider).
  """
  resolved_adapter = adapter or get_gen_model_adapter(provider)
  for rp in rendered_prompts:
    yield run_one_generation(
      resolved_adapter,
      rp,
      provider=provider,
      model_name=model_name,
      generation_params=generation_params,
    )


def run_generation(
  rendered_prompts: list[RenderedPrompt],
  *,
  provider: str,
  model_name: str,
  generation_params: dict[str, object] | None = None,
  adapter: GenerationAdapter | None = None,
) -> list[ModelOutputRow]:
  """
  Materialize all ModelOutputRow rows into a list.
  (For day5 small datasets this is fine; for large datasets prefer iter_generation_outputs.)
  """
  return list(
    iter_generation_outputs(
      rendered_prompts,
      provider=provider,
      model_name=model_name,
      generation_params=generation_params,
      adapter=adapter,
    )
  )
