from dataclasses import asdict, dataclass
from typing import Any, Optional


FIELD_LIMITS = {
    "host": 255,
    "os_type": 50,
    "event_type": 100,
    "event_code": 100,
    "category": 100,
    "severity": 50,
    "username": 255,
    "ip_address": 100,
    "message": 2000,
    "source": 255,
}


@dataclass
class AgentEvent:
    ts: str
    host: str
    os_type: Optional[str]
    event_type: str
    event_code: Optional[str]
    category: Optional[str]
    severity: str
    username: Optional[str]
    ip_address: Optional[str]
    message: str
    source: Optional[str]
    raw_data: Optional[dict[str, Any]] = None

    def model_dump(self) -> dict[str, Any]:
        payload = asdict(self)
        for field_name, limit in FIELD_LIMITS.items():
            value = payload.get(field_name)
            if isinstance(value, str) and len(value) > limit:
                payload[field_name] = value[: limit - 3] + "..."
        return payload
