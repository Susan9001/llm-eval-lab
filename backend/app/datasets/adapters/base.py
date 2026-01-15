from collections.abc import Callable
from typing import Protocol

from app.datasets.dataset_types import RawRow, SampleRecord


class DatasetAdapter(Protocol):
  def adapt(self, row: RawRow, row_index: int) -> SampleRecord: ...


DatasetAdapterBuilder = Callable[..., DatasetAdapter]

ADAPTER_REGISTRY: dict[str, DatasetAdapterBuilder] = {}


def register_adapter(adapter_name: str, builder: DatasetAdapterBuilder) -> None:
  ADAPTER_REGISTRY[adapter_name] = builder


def build_dataset_adapter(adapter_name: str, **kwargs) -> DatasetAdapter:
  name = adapter_name.lower().strip()
  if name not in ADAPTER_REGISTRY:
    known = ", ".join(sorted(ADAPTER_REGISTRY.keys()))
    raise ValueError(f"Unknown adapter_name '{name}'. Known: {known}")
  return ADAPTER_REGISTRY[name](**kwargs)
