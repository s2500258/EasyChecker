import json
from typing import Any
from urllib import error, request

from config import get_settings
from schemas import AgentEvent


# Transport layer for sending normalized agent events to the backend API.
def send_event(event: AgentEvent) -> dict[str, Any]:
    # Serialize the event exactly once before sending it as JSON over HTTP.
    payload = event.model_dump()
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        get_settings().backend_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        # Preserve backend validation details so they are visible in the agent logs.
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Backend returned HTTP {exc.code}: {details}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Could not connect to backend: {exc.reason}") from exc
