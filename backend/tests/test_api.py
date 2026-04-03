import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.models import init_db


def _reset_database() -> None:
    # Reset SQLite tables so each test starts from a clean state.
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
    # Build realistic event data that should trigger the backend rule.
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


def _suspicious_process_payload(offset_seconds: int) -> dict:
    timestamp = (
        datetime.now(timezone.utc) - timedelta(minutes=4, seconds=offset_seconds)
    ).isoformat().replace("+00:00", "Z")
    return {
        "ts": timestamp,
        "host": "WIN-LAB-02",
        "os_type": "windows",
        "event_type": "process",
        "event_code": "4688",
        "category": "process_created",
        "severity": "HIGH",
        "username": "pytest-analyst",
        "ip_address": None,
        "message": "Process powershell.exe was created",
        "source": "pytest",
        "raw_data": {
            "provider": "Security",
            "process_name": "powershell.exe",
            "command_line": "powershell.exe -ExecutionPolicy Bypass",
        },
    }


def _critical_service_payload() -> dict:
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "ts": timestamp,
        "host": "WIN-OPS-03",
        "os_type": "windows",
        "event_type": "system",
        "event_code": "7036",
        "category": "service_stopped",
        "severity": "HIGH",
        "username": None,
        "ip_address": None,
        "message": "Windows Defender service stopped",
        "source": "pytest",
        "raw_data": {
            "provider": "Service Control Manager",
            "service_name": "Windows Defender",
            "state": "stopped",
        },
    }


def test_ingest_events_and_generate_one_alert() -> None:
    # End-to-end test for ingest, storage, listing, and alert generation.
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
    # Validation test: required event fields must be present.
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


def test_ingest_generates_process_and_service_alerts() -> None:
    _reset_database()

    with TestClient(app) as client:
        for offset in range(50, 47, -1):
            response = client.post(
                "/api/v1/ingest", json=_suspicious_process_payload(offset)
            )
            assert response.status_code == 200

        service_response = client.post("/api/v1/ingest", json=_critical_service_payload())
        assert service_response.status_code == 200

        alerts_response = client.get("/api/v1/alerts")

    alerts = alerts_response.json()
    alert_types = {alert["type"] for alert in alerts}

    assert "Suspicious process burst" in alert_types
    assert "Critical service stopped" in alert_types


def test_hosts_endpoint_returns_aggregated_host_summaries() -> None:
    _reset_database()

    with TestClient(app) as client:
        for offset in range(50, 45, -1):
            response = client.post("/api/v1/ingest", json=_failed_login_payload(offset))
            assert response.status_code == 200

        for offset in range(50, 47, -1):
            response = client.post(
                "/api/v1/ingest", json=_suspicious_process_payload(offset)
            )
            assert response.status_code == 200

        response = client.post("/api/v1/ingest", json=_critical_service_payload())
        assert response.status_code == 200

        hosts_response = client.get("/api/v1/hosts")

    hosts = hosts_response.json()
    by_host = {host["host"]: host for host in hosts}

    assert hosts_response.status_code == 200
    assert {"WIN-PC-01", "WIN-LAB-02", "WIN-OPS-03"}.issubset(by_host.keys())
    assert by_host["WIN-PC-01"]["total_events"] == 5
    assert by_host["WIN-PC-01"]["total_alerts"] == 1
    assert by_host["WIN-PC-01"]["highest_severity"] == "MEDIUM"
    assert by_host["WIN-PC-01"]["last_event_type"] == "authentication"
    assert by_host["WIN-LAB-02"]["total_events"] == 3
    assert by_host["WIN-LAB-02"]["total_alerts"] == 1
    assert by_host["WIN-LAB-02"]["highest_severity"] == "HIGH"
    assert by_host["WIN-OPS-03"]["total_events"] == 1
    assert by_host["WIN-OPS-03"]["total_alerts"] == 1
    assert by_host["WIN-OPS-03"]["highest_severity"] == "HIGH"
