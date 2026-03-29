import json
from datetime import datetime, timedelta, timezone
from urllib import request


API_URL = "http://127.0.0.1:8000/api/v1/ingest"


def send_event(index: int) -> None:
    ts = (
        datetime.now(timezone.utc) - timedelta(minutes=4, seconds=50 - index)
    ).isoformat().replace("+00:00", "Z")

    payload = {
        "ts": ts,
        "host": "WIN-PC-01",
        "os_type": "windows",
        "event_type": "authentication",
        "event_code": "4625",
        "category": "login_failure",
        "severity": "MEDIUM",
        "username": "student",
        "ip_address": "192.168.1.50",
        "message": "Failed login attempt",
        "source": "manual_test",
        "raw_data": {
            "provider": "Security",
            "logon_type": 3,
            "status": "0xC000006D",
        },
    }

    req = request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req) as response:
        print(response.read().decode("utf-8"))


if __name__ == "__main__":
    for i in range(5):
        send_event(i)
