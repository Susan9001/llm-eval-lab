from collections.abc import Callable
from typing import Any, TypedDict


class SampleRecord(TypedDict, total=False):
  source_sample_id: str
  input_text: str
  reference_output: str | None
  metadata: dict[str, Any] | None


RawRow = dict[str, Any]

AdapterFn = Callable[[RawRow, int], SampleRecord]
