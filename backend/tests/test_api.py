import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.models import init_db


def _reset_database() -> None:
    init_db()
    db_path = Path(get_settings().sqlite_db_path)
    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM alerts")
        cursor.execute("DELETE FROM events")
        connection.commit()
    finally:
        connection.close()


def _failed_login_payload(offset_seconds: int) -> dict:
    timestamp = (
        datetime.now(timezone.utc) - timedelta(minutes=4, seconds=offset_seconds)
    ).isoformat().replace("+00:00", "Z")
    return {
        "ts": timestamp,
        "host": "WIN-PC-01",
        "os_type": "windows",
        "event_type": "authentication",
        "event_code": "4625",
        "category": "login_failure",
        "severity": "MEDIUM",
        "username": "pytest-user",
        "ip_address": "10.0.0.15",
        "message": "Failed login attempt",
        "source": "pytest",
        "raw_data": {"provider": "Security", "reason": "bad password"},
    }


def test_ingest_events_and_generate_one_alert() -> None:
    _reset_database()

    with TestClient(app) as client:
        responses = []
        for offset in range(50, 45, -1):
            response = client.post("/api/v1/ingest", json=_failed_login_payload(offset))
            assert response.status_code == 200
            responses.append(response.json())

        events_response = client.get("/api/v1/events")
        alerts_response = client.get("/api/v1/alerts")

    events = events_response.json()
    alerts = alerts_response.json()

    assert len(events) == 5
    assert len(alerts) == 1
    assert responses[-1]["alerts"][0]["type"] == "Brute force attempt"
    assert alerts[0]["host"] == "WIN-PC-01"
    assert alerts[0]["event_count"] == 5
    assert events[0]["os_type"] == "windows"
    assert events[0]["event_code"] == "4625"
    assert events[0]["category"] == "login_failure"
    assert events[0]["username"] == "pytest-user"
    assert events[0]["ip_address"] == "10.0.0.15"
    assert events[0]["raw_data"]["provider"] == "Security"


def test_ingest_rejects_invalid_payload() -> None:
    _reset_database()

    invalid_payload = {
        "host": "WIN-PC-01",
        "event_type": "authentication",
        "severity": "MEDIUM",
        "message": "Failed login attempt",
    }

    with TestClient(app) as client:
        response = client.post("/api/v1/ingest", json=invalid_payload)

    assert response.status_code == 422
