from dataclasses import asdict, dataclass
from typing import Any, Optional


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
        return asdict(self)
