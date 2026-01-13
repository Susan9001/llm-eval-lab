from typing import TypedDict
from app.datasets.dataset_types import DatasetSnapshotIdentifier


class GenerationRequest(TypedDict):
  rendered_prompt: str
  provider: str
  model_name: str
  generation_params: dict[str, object]


class Usage(TypedDict):
  prompt_tokens: int | None
  completion_tokens: int | None
  total_tokens: int | None
  provider_request_id: str | None
  finish_reason: str | None
  cost_usd: float | None


class GenerationResponse(TypedDict):
  output_text: str | None
  generation_status: str
  generation_error_message: str | None
  usage_json: Usage


class ModelOutputRow(DatasetSnapshotIdentifier):
  model_output_uuid: str
  source_sample_id: str

  prompt_group_uid: str
  prompt_version: str
  prompt_path: str | None

  provider: str
  model_name: str
  generation_params: dict[str, object]

  output_text: str | None
  generation_status: str
  generation_error_message: str | None

  usage_json: Usage

  started_at: str
  finished_at: str
  latency_ms: int | None
