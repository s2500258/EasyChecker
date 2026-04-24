from datetime import timedelta
from typing import Any, Optional

from ..config import get_settings
from ..db import db_cursor
from ..utils import parse_event_timestamp, utc_now_iso


def evaluate_event_rules(
    *,
    host: str,
    event_type: str,
    event_code: Optional[str],
    category: Optional[str],
    severity: str,
    message: str,
    raw_data: Optional[dict[str, Any]],
) -> list[dict]:
    # Apply a few small MVP rules that match the simulated fleet scenarios.
    settings = get_settings()
    alerts = []

    if _is_failed_login_event(
        event_type=event_type,
        event_code=event_code,
        category=category,
        message=message,
    ):
        latest_matches = _count_recent_failed_logins(host=host)
        if latest_matches == settings.failed_login_threshold:
            alerts.append(
                _create_alert(
                    alert_type="Brute force attempt",
                    severity="HIGH",
                    host=host,
                    message=(
                        f"{latest_matches} failed logins detected from {host} "
                        f"within {settings.failed_login_window_minutes} minutes."
                    ),
                    event_count=latest_matches,
                )
            )

    if (
        event_type == "process"
        and category == "process_created"
        and severity.upper() == "HIGH"
    ):
        latest_matches = _count_recent_suspicious_processes(host=host)
        if latest_matches == settings.suspicious_process_threshold:
            alerts.append(
                _create_alert(
                    alert_type="Suspicious process burst",
                    severity="HIGH",
                    host=host,
                    message=(
                        f"{latest_matches} high-severity process creation events detected "
                        f"on {host} within {settings.suspicious_process_window_minutes} minutes."
                    ),
                    event_count=latest_matches,
                )
            )

    service_name = (raw_data or {}).get("service_name")
    if category == "service_stopped" and service_name in {"Windows Defender", "Security Center"}:
        alerts.append(
            _create_alert(
                alert_type="Critical service stopped",
                severity="HIGH",
                host=host,
                message=f"{service_name} stopped on {host}.",
                event_count=1,
            )
        )

    return alerts


def _count_recent_failed_logins(*, host: str) -> int:
    # Count failures relative to the newest relevant event for the host.
    settings = get_settings()

    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT ts, event_type, event_code, category, message
            FROM events
            WHERE host = ?
            ORDER BY ts DESC
            """,
            (host,),
        )
        rows = cursor.fetchall()

    now = None
    window = timedelta(minutes=settings.failed_login_window_minutes)
    count = 0

    for row in rows:
        if not _is_failed_login_event(
            event_type=row["event_type"],
            event_code=row["event_code"],
            category=row["category"],
            message=row["message"],
        ):
            continue

        event_time = parse_event_timestamp(row["ts"])
        if now is None:
            now = event_time

        if now - event_time <= window:
            count += 1

    return count


def _count_recent_suspicious_processes(*, host: str) -> int:
    # Count high-severity process creation events within the configured window.
    settings = get_settings()

    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT ts, event_type, category, severity
            FROM events
            WHERE host = ?
            ORDER BY ts DESC
            """,
            (host,),
        )
        rows = cursor.fetchall()

    now = None
    window = timedelta(minutes=settings.suspicious_process_window_minutes)
    count = 0

    for row in rows:
        if row["event_type"] != "process":
            continue
        if row["category"] != "process_created":
            continue
        if (row["severity"] or "").upper() != "HIGH":
            continue

        event_time = parse_event_timestamp(row["ts"])
        if now is None:
            now = event_time

        if now - event_time <= window:
            count += 1

    return count


def _create_alert(
    *,
    alert_type: str,
    severity: str,
    host: str,
    message: str,
    event_count: int,
) -> dict[str, Any]:
    # Store the generated alert and return the saved record for the API response.
    alert = {
        "type": alert_type,
        "severity": severity,
        "host": host,
        "message": message,
        "created_at": utc_now_iso(),
        "event_count": event_count,
    }

    with db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO alerts (type, severity, host, message, created_at, event_count)
            VALUES (:type, :severity, :host, :message, :created_at, :event_count)
            """,
            alert,
        )
        alert["id"] = cursor.lastrowid

    return alert


def _is_failed_login_event(
    *,
    event_type: Optional[str],
    event_code: Optional[str],
    category: Optional[str],
    message: Optional[str],
) -> bool:
    # Prefer normalized event fields because they are stable across Windows
    # locale changes, then fall back to the human-readable message text.
    if (event_code or "").strip() == "4625":
        return True
    if (category or "").strip().lower() == "login_failure":
        return True
    if (event_type or "").strip().lower() != "authentication":
        return False
    return "failed login" in (message or "").lower()
