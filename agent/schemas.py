from dataclasses import asdict, dataclass
from typing import Any, Optional


# These limits mirror the backend schema so the agent can trim oversized strings
# before they trigger HTTP 422 validation errors during ingest.
FIELD_LIMITS = {
    "host": 255,
    "host_ip": 100,
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


"""Normalized event model shared across the agent pipeline."""
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
    # Keep host_ip optional with a default so older call sites or partially
    # updated agent files do not crash during live collection.
    host_ip: Optional[str] = None
    raw_data: Optional[dict[str, Any]] = None

    def model_dump(self) -> dict[str, Any]:
        # Convert the dataclass to a plain JSON-ready dict and enforce field limits.
        payload = asdict(self)
        for field_name, limit in FIELD_LIMITS.items():
            value = payload.get(field_name)
            if isinstance(value, str) and len(value) > limit:
                payload[field_name] = value[: limit - 3] + "..."
        return payload
