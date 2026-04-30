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
    settings = get_settings()
    db_path = Path(get_settings().sqlite_db_path)
    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM alert_events")
        cursor.execute("DELETE FROM alerts")
        cursor.execute("DELETE FROM events")
        cursor.execute("DELETE FROM rule_settings")
        cursor.execute(
            """
            INSERT INTO rule_settings (key, value) VALUES (?, ?)
            """,
            ("failed_login_threshold", str(settings.failed_login_threshold)),
        )
        cursor.execute(
            """
            INSERT INTO rule_settings (key, value) VALUES (?, ?)
            """,
            ("failed_login_window_minutes", str(settings.failed_login_window_minutes)),
        )
        cursor.execute(
            """
            INSERT INTO rule_settings (key, value) VALUES (?, ?)
            """,
            ("suspicious_process_threshold", str(settings.suspicious_process_threshold)),
        )
        cursor.execute(
            """
            INSERT INTO rule_settings (key, value) VALUES (?, ?)
            """,
            (
                "suspicious_process_window_minutes",
                str(settings.suspicious_process_window_minutes),
            ),
        )
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
        "host_ip": "192.168.5.101",
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


def _localized_failed_login_payload(offset_seconds: int) -> dict:
    payload = _failed_login_payload(offset_seconds)
    payload["message"] = "Не удалось выполнить вход в учетную запись."
    return payload


def _suspicious_process_payload(offset_seconds: int) -> dict:
    timestamp = (
        datetime.now(timezone.utc) - timedelta(minutes=4, seconds=offset_seconds)
    ).isoformat().replace("+00:00", "Z")
    return {
        "ts": timestamp,
        "host": "WIN-LAB-02",
        "host_ip": "192.168.5.102",
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
        "host_ip": "192.168.5.103",
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
            "service_key": "windows_defender",
            "state": "stopped",
        },
    }


def _localized_critical_service_payload() -> dict:
    payload = _critical_service_payload()
    payload["host"] = "WIN-FI-04"
    payload["host_ip"] = "192.168.5.104"
    payload["message"] = "Microsoft Defender -palvelu siirtyi pysaytetty-tilaan."
    payload["raw_data"] = {
        "provider": "Service Control Manager",
        "service_name": "Turvakeskus",
        "service_key": "security_center",
        "state": "pysaytetty",
    }
    return payload


def _snapshot_critical_service_payload() -> dict:
    payload = _critical_service_payload()
    payload["host"] = "WIN-LIVE-05"
    payload["host_ip"] = "192.168.5.105"
    payload["event_code"] = "SERVICE_STATE_POLL"
    payload["source"] = "windows_service_snapshot"
    payload["raw_data"] = {
        "provider": "Service Control Manager",
        "service_name": "Windows Defender",
        "service_internal_name": "WinDefend",
        "service_key": "windows_defender",
        "state": "stopped",
        "previous_state": "running",
        "detection_method": "service_snapshot",
    }
    return payload


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
    assert len(alerts[0]["event_ids"]) == 5
    assert events[0]["os_type"] == "windows"
    assert events[0]["host_ip"] == "192.168.5.101"
    assert events[0]["event_code"] == "4625"
    assert events[0]["category"] == "login_failure"
    assert events[0]["username"] == "pytest-user"
    assert events[0]["ip_address"] == "10.0.0.15"
    assert events[0]["raw_data"]["provider"] == "Security"


def test_ingest_generates_bruteforce_alert_for_localized_failed_login_messages() -> None:
    _reset_database()

    with TestClient(app) as client:
        for offset in range(50, 45, -1):
            response = client.post(
                "/api/v1/ingest", json=_localized_failed_login_payload(offset)
            )
            assert response.status_code == 200

        alerts_response = client.get("/api/v1/alerts")

    alerts = alerts_response.json()

    assert any(alert["type"] == "Brute force attempt" for alert in alerts)
    localized_alert = next(
        alert for alert in alerts if alert["type"] == "Brute force attempt"
    )
    assert len(localized_alert["event_ids"]) == 5


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


def test_failed_login_rule_can_be_updated_via_api() -> None:
    _reset_database()

    with TestClient(app) as client:
        get_response = client.get("/api/v1/rules/failed-login")
        assert get_response.status_code == 200
        assert get_response.json()["failed_login_threshold"] == 5

        update_response = client.put(
            "/api/v1/rules/failed-login",
            json={
                "failed_login_threshold": 3,
                "failed_login_window_minutes": 10,
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["failed_login_threshold"] == 3
        assert update_response.json()["failed_login_window_minutes"] == 10

        for offset in range(50, 47, -1):
            response = client.post("/api/v1/ingest", json=_failed_login_payload(offset))
            assert response.status_code == 200

        alerts_response = client.get("/api/v1/alerts")

    alerts = alerts_response.json()
    assert any(alert["type"] == "Brute force attempt" for alert in alerts)


def test_suspicious_process_rule_can_be_updated_via_api() -> None:
    _reset_database()

    with TestClient(app) as client:
        get_response = client.get("/api/v1/rules/suspicious-process")
        assert get_response.status_code == 200
        assert get_response.json()["suspicious_process_threshold"] == 3

        update_response = client.put(
            "/api/v1/rules/suspicious-process",
            json={
                "suspicious_process_threshold": 2,
                "suspicious_process_window_minutes": 10,
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["suspicious_process_threshold"] == 2
        assert update_response.json()["suspicious_process_window_minutes"] == 10

        for offset in range(50, 48, -1):
            response = client.post(
                "/api/v1/ingest", json=_suspicious_process_payload(offset)
            )
            assert response.status_code == 200

        alerts_response = client.get("/api/v1/alerts")

    alerts = alerts_response.json()
    assert any(alert["type"] == "Suspicious process burst" for alert in alerts)


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
    process_alert = next(
        alert for alert in alerts if alert["type"] == "Suspicious process burst"
    )
    service_alert = next(
        alert for alert in alerts if alert["type"] == "Critical service stopped"
    )
    assert len(process_alert["event_ids"]) == 3
    assert len(service_alert["event_ids"]) == 1


def test_ingest_generates_service_alert_for_localized_service_data() -> None:
    _reset_database()

    with TestClient(app) as client:
        response = client.post("/api/v1/ingest", json=_localized_critical_service_payload())
        assert response.status_code == 200

        alerts_response = client.get("/api/v1/alerts")

    alerts = alerts_response.json()

    assert any(alert["type"] == "Critical service stopped" for alert in alerts)
    localized_service_alert = next(
        alert for alert in alerts if alert["type"] == "Critical service stopped"
    )
    assert len(localized_service_alert["event_ids"]) == 1


def test_ingest_generates_service_alert_for_snapshot_based_service_stop() -> None:
    _reset_database()

    with TestClient(app) as client:
        response = client.post("/api/v1/ingest", json=_snapshot_critical_service_payload())
        assert response.status_code == 200

        alerts_response = client.get("/api/v1/alerts")

    alerts = alerts_response.json()

    snapshot_service_alert = next(
        alert for alert in alerts if alert["type"] == "Critical service stopped"
    )
    assert snapshot_service_alert["host"] == "WIN-LIVE-05"
    assert len(snapshot_service_alert["event_ids"]) == 1


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
    assert by_host["WIN-PC-01"]["host_ip"] == "192.168.5.101"
    assert by_host["WIN-PC-01"]["total_alerts"] == 1
    assert by_host["WIN-PC-01"]["highest_severity"] == "HIGH"
    assert by_host["WIN-PC-01"]["last_event_type"] == "authentication"
    assert by_host["WIN-LAB-02"]["total_events"] == 3
    assert by_host["WIN-LAB-02"]["host_ip"] == "192.168.5.102"
    assert by_host["WIN-LAB-02"]["total_alerts"] == 1
    assert by_host["WIN-LAB-02"]["highest_severity"] == "HIGH"
    assert by_host["WIN-OPS-03"]["total_events"] == 1
    assert by_host["WIN-OPS-03"]["host_ip"] == "192.168.5.103"
    assert by_host["WIN-OPS-03"]["total_alerts"] == 1
    assert by_host["WIN-OPS-03"]["highest_severity"] == "HIGH"
