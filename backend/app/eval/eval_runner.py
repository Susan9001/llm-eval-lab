from __future__ import annotations

from collections.abc import Iterable, Iterator
from time import perf_counter

from app.eval.eval_types import EvalRequest, EvalResultRow, JudgeType
from app.eval.judges.adapters.base import build_judge_adapter
from app.eval.statuses import EVAL_STATUS_FAILED
from app.generation.generation_types import ModelOutputRow
from app.prompts.prompt_types import RenderedPrompt
from app.utils.time_utils import utc_now_iso8601


RenderedPromptIdKey = tuple[str, str, str, str, str, str]


def make_rendered_prompt_key(
  obj: RenderedPrompt | ModelOutputRow,
) -> RenderedPromptIdKey:
  return (
    obj["dataset_group_uid"],
    obj["dataset_version"],
    obj["split"],
    obj["source_sample_id"],
    obj["prompt_group_uid"],
    obj["prompt_version"],
  )


def index_rendered_prompts(
  rendered_prompts: Iterable[RenderedPrompt],
) -> dict[RenderedPromptIdKey, RenderedPrompt]:
  """
  Build an index from RenderedPromptKey to RenderedPrompt.

  Duplicate keys indicate pipeline issues and should fail fast.
  """
  rendered_prompts_by_key: dict[RenderedPromptIdKey, RenderedPrompt] = {}
  for rp in rendered_prompts:
    key = make_rendered_prompt_key(rp)
    if key in rendered_prompts_by_key:
      existing = rendered_prompts_by_key[key]
      raise ValueError(
        f"Duplicate rendered prompt key detected. key={key}, "
        f"existing_prompt_path={existing.get('prompt_path')}, "
        f"new_prompt_path={rp.get('prompt_path')}"
      )
    rendered_prompts_by_key[key] = rp
  return rendered_prompts_by_key


def build_eval_request(rp: RenderedPrompt, mo: ModelOutputRow) -> EvalRequest:
  """
  Build EvalRequest by joining RenderedPrompt and ModelOutputRow.

  prompt_path is taken from model output if present, otherwise fallback to rendered prompt.
  """
  prompt_path = mo.get("prompt_path")
  if prompt_path is None:
    prompt_path = rp.get("prompt_path")

  return EvalRequest(
    dataset_group_uid=rp["dataset_group_uid"],
    dataset_version=rp["dataset_version"],
    split=rp["split"],
    source_sample_id=rp["source_sample_id"],
    prompt_group_uid=rp["prompt_group_uid"],
    prompt_version=rp["prompt_version"],
    prompt_path=prompt_path,
    # Model output identity
    model_output_uuid=mo["model_output_uuid"],
    # Model identity
    provider=mo["provider"],
    model_name=mo["model_name"],
    generation_params=mo.get("generation_params"),
    # Generation status
    generation_status=mo["generation_status"],
    generation_error_message=mo.get("generation_error_message"),
    # Payloads for judging
    input_text=rp.get("input_text"),
    reference_output=rp.get("reference_output"),
    output_text=mo.get("output_text"),
    # For LLM-as-judge only (kept for extensibility)
    rendered_eval_prompt=None,
  )


def build_failed_eval_result(
  req: EvalRequest,
  *,
  judge_type: JudgeType,
  judge_name: str,
  judge_version: str | None,
  error_message: str,
) -> EvalResultRow:
  """
  Build a minimal EvalResultRow when adapter.evaluate raises unexpectedly.
  """
  return EvalResultRow(
    dataset_group_uid=req["dataset_group_uid"],
    dataset_version=req["dataset_version"],
    split=req["split"],
    source_sample_id=req["source_sample_id"],
    prompt_group_uid=req["prompt_group_uid"],
    prompt_version=req["prompt_version"],
    prompt_path=req.get("prompt_path"),
    model_output_uuid=req["model_output_uuid"],
    provider=req["provider"],
    model_name=req["model_name"],
    judge_type=judge_type,
    judge_name=judge_name,
    judge_version=judge_version,
    eval_status=EVAL_STATUS_FAILED,
    eval_error_message=error_message,
    rule_outcomes={},
    primary_score_rule=None,
    primary_score=None,
    # Runner will overwrite timing fields
    started_at=utc_now_iso8601(),
    finished_at=utc_now_iso8601(),
    latency_ms=0,
  )


def run_one_eval(
  adapter,
  rp: RenderedPrompt,
  mo: ModelOutputRow,
  *,
  judge_type: JudgeType,
  judge_name: str,
  judge_version: str | None,
) -> EvalResultRow:
  """
  Evaluate one joined (RenderedPrompt, ModelOutputRow) pair.

  Timing is owned by the runner, not adapters.
  """
  req = build_eval_request(rp, mo)

  started_at = utc_now_iso8601()
  start_perf = perf_counter()

  try:
    res: EvalResultRow = adapter.evaluate(req)
  except Exception as e:
    res = build_failed_eval_result(
      req,
      judge_type=judge_type,
      judge_name=judge_name,
      judge_version=judge_version,
      error_message=f"{type(e).__name__}: {e}",
    )

  finished_at = utc_now_iso8601()
  latency_ms = max(int((perf_counter() - start_perf) * 1000), 0)

  # Runner enforces identity and timing fields for consistency
  res["dataset_group_uid"] = req["dataset_group_uid"]
  res["dataset_version"] = req["dataset_version"]
  res["split"] = req["split"]
  res["source_sample_id"] = req["source_sample_id"]
  res["prompt_group_uid"] = req["prompt_group_uid"]
  res["prompt_version"] = req["prompt_version"]
  res["prompt_path"] = req.get("prompt_path")

  res["model_output_uuid"] = req["model_output_uuid"]
  res["provider"] = req["provider"]
  res["model_name"] = req["model_name"]

  res["judge_type"] = judge_type
  res["judge_name"] = judge_name
  res["judge_version"] = judge_version

  res["started_at"] = started_at
  res["finished_at"] = finished_at
  res["latency_ms"] = latency_ms
  return res


def iter_eval_results(
  rendered_prompts: Iterable[RenderedPrompt],
  model_output_rows: Iterable[ModelOutputRow],
  *,
  judge_type: JudgeType,
  judge_name: str,
  judge_version: str | None = None,
  judge_adapter_kwargs: dict[str, object] | None = None,
) -> Iterator[EvalResultRow]:
  """
  Yield EvalResultRow rows one by one.
  """
  rendered_prompts_by_key = index_rendered_prompts(rendered_prompts)
  adapter = build_judge_adapter(judge_type, **(judge_adapter_kwargs or {}))

  for mo in model_output_rows:
    key = make_rendered_prompt_key(mo)
    rp = rendered_prompts_by_key.get(key)
    if rp is None:
      raise ValueError(
        "Missing rendered prompt for model output row. "
        f"model_output_uuid={mo['model_output_uuid']}, "
        f"provider={mo['provider']}, "
        f"model_name={mo['model_name']}, "
        f"rendered_prompt_key={key}"
      )

    yield run_one_eval(
      adapter,
      rp,
      mo,
      judge_type=judge_type,
      judge_name=judge_name,
      judge_version=judge_version,
    )


def run_eval(
  rendered_prompts: list[RenderedPrompt],
  model_output_rows: list[ModelOutputRow],
  *,
  judge_type: JudgeType,
  judge_name: str,
  judge_version: str | None = None,
  judge_adapter_kwargs: dict[str, object] | None = None,
) -> list[EvalResultRow]:
  """
  Materialize all EvalResultRow rows into a list.
  """
  return list(
    iter_eval_results(
      rendered_prompts,
      model_output_rows,
      judge_type=judge_type,
      judge_name=judge_name,
      judge_version=judge_version,
      judge_adapter_kwargs=judge_adapter_kwargs,
    )
  )
