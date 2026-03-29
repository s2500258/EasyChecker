import json
from datetime import datetime, timezone
from typing import Any, Optional


def parse_event_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def dump_raw_data(value: Optional[dict[str, Any]]) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(value)


def load_raw_data(value: Optional[str]) -> Optional[dict[str, Any]]:
    if value is None:
        return None
    return json.loads(value)
