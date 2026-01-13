# backend/app/generation/adapters/base.py
from typing import Protocol

from app.generation.generation_types import (
  GenerationRequest,
  GenerationResponse,
)


class GenerationAdapter(Protocol):
  def generate(self, req: GenerationRequest) -> GenerationResponse: ...


ADAPTER_REGISTRY: dict[str, GenerationAdapter] = {}


def register_adapter(provider: str, adapter: GenerationAdapter) -> None:
  ADAPTER_REGISTRY[provider] = adapter


def get_adapter(provider: str) -> GenerationAdapter:
  if provider not in ADAPTER_REGISTRY:
    known = ", ".join(sorted(ADAPTER_REGISTRY.keys()))
    raise ValueError(f"Unknown provider '{provider}'. Known: {known}")
  return ADAPTER_REGISTRY[provider]
