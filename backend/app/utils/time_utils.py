from datetime import datetime, timezone

_ISO_Z_SUFFIX = "Z"


def utc_now_iso8601() -> str:
  return (
    datetime.now(timezone.utc)
    .replace(microsecond=0)
    .isoformat()
    .replace("+00:00", "Z")
  )


def parse_utc_iso8601(ts: str) -> datetime:
  # Expect "YYYY-MM-DDTHH:MM:SSZ"
  if not ts.endswith(_ISO_Z_SUFFIX):
    raise ValueError(f"Expected UTC timestamp ending with 'Z', got: {ts}")
  # Convert "Z" -> "+00:00" for datetime.fromisoformat
  return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(
    timezone.utc
  )
