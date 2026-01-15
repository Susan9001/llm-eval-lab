import hashlib
from time import sleep

from app.common.statuses import GENERATION_STATUS_SUCCEEDED
from app.generation.generation_types import (
  GenerationRequest,
  GenerationResponse,
  Usage,
)


class HarmfulScoreAdapter:
  """
  A simple synthetic generator for binary harmfulness.

  Output is a single char: "0" or "1".
  Deterministic per rendered_prompt (and optional seed) so results are stable.
  """

  def generate(self, req: GenerationRequest) -> GenerationResponse:
    sleep(0.02)

    generation_params = req["generation_params"]
    seed = int(generation_params.get("seed", 0))
    harmful_prob = float(generation_params.get("harmful_prob", 0.5))

    # Deterministic pseudo-random in [0, 1) based on (seed + rendered_prompt).
    payload = f"{seed}:{req['rendered_prompt']}".encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    value_int = int.from_bytes(digest[:8], byteorder="big", signed=False)
    rand01 = value_int / float(2**64)
    output_text = "1" if rand01 < harmful_prob else "0"

    usage = Usage(
      prompt_tokens=10,
      completion_tokens=1,
      total_tokens=11,
      provider_request_id=None,
      finish_reason="stop",
      cost_usd=0.0,
    )
    return GenerationResponse(
      output_text=output_text,
      generation_status=GENERATION_STATUS_SUCCEEDED,
      generation_error_message=None,
      usage_json=usage,
    )
