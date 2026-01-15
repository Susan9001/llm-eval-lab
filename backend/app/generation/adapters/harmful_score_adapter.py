import hashlib
import json
from time import sleep

from app.common.statuses import GENERATION_STATUS_SUCCEEDED
from app.generation.generation_types import (
  GenerationRequest,
  GenerationResponse,
  Usage,
)


class HarmfulScoreAdapter:
  """
  Synthetic generator that outputs a continuous harmfulness score in JSON.

  output_text example: {"harmful_prob":0.7321}
  """

  def generate(self, req: GenerationRequest) -> GenerationResponse:
    sleep(0.02)

    seed = int(req["generation_params"].get("seed", 0))

    payload = f"{seed}:{req['rendered_prompt']}".encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    value_int = int.from_bytes(digest[:8], byteorder="big", signed=False)
    rand01 = value_int / float(2**64)

    harmful_prob = round(rand01, 4)
    output_text = json.dumps(
      {"harmful_prob": harmful_prob},
      separators=(",", ":"),
      sort_keys=True,
    )

    usage = Usage(
      prompt_tokens=10,
      completion_tokens=5,
      total_tokens=15,
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
