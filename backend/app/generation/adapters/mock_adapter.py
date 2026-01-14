from time import sleep
from app.generation.generation_types import (
  GenerationRequest,
  GenerationResponse,
  Usage,
)
from app.generation.statuses import GENERATION_STATUS_SUCCEEDED


class MockAdapter:
  def generate(self, req: GenerationRequest) -> GenerationResponse:
    sleep(0.1)
    usage: Usage = Usage(
      prompt_tokens=10,
      completion_tokens=20,
      total_tokens=30,
      provider_request_id=None,
      finish_reason=None,
      cost_usd=0.01,
    )
    return GenerationResponse(
      output_text="Mock output text",
      generation_status=GENERATION_STATUS_SUCCEEDED,
      generation_error_message=None,
      usage_json=usage,
    )
