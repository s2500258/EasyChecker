from datetime import timedelta
from typing import Any, Optional

from ..config import get_settings
from ..db import db_cursor
from ..utils import parse_event_timestamp, utc_now_iso


def evaluate_event_rules(
    *,
    event_id: int,
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
        matching_event_ids = _find_recent_failed_login_event_ids(host=host)
        if len(matching_event_ids) == settings.failed_login_threshold:
            alerts.append(
                _create_alert(
                    alert_type="Brute force attempt",
                    severity="HIGH",
                    host=host,
                    message=(
                        f"{len(matching_event_ids)} failed logins detected from {host} "
                        f"within {settings.failed_login_window_minutes} minutes."
                    ),
                    event_count=len(matching_event_ids),
                    event_ids=matching_event_ids,
                )
            )

    if (
        event_type == "process"
        and category == "process_created"
        and severity.upper() == "HIGH"
    ):
        matching_event_ids = _find_recent_suspicious_process_event_ids(host=host)
        if len(matching_event_ids) == settings.suspicious_process_threshold:
            alerts.append(
                _create_alert(
                    alert_type="Suspicious process burst",
                    severity="HIGH",
                    host=host,
                    message=(
                        f"{len(matching_event_ids)} high-severity process creation events detected "
                        f"on {host} within {settings.suspicious_process_window_minutes} minutes."
                    ),
                    event_count=len(matching_event_ids),
                    event_ids=matching_event_ids,
                )
            )

    service_key = _classify_critical_service(
        service_key=(raw_data or {}).get("service_key"),
        service_name=(raw_data or {}).get("service_name"),
    )
    if category == "service_stopped" and service_key:
        alerts.append(
            _create_alert(
                alert_type="Critical service stopped",
                severity="HIGH",
                host=host,
                message=f"{_service_label(service_key)} stopped on {host}.",
                event_count=1,
                event_ids=[event_id],
            )
        )

    return alerts


def _find_recent_failed_login_event_ids(*, host: str) -> list[int]:
    # Return the exact event IDs that currently form the failed-login window.
    settings = get_settings()

    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, ts, event_type, event_code, category, message
            FROM events
            WHERE host = ?
            ORDER BY ts DESC
            """,
            (host,),
        )
        rows = cursor.fetchall()

    now = None
    window = timedelta(minutes=settings.failed_login_window_minutes)
    event_ids = []

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
            event_ids.append(row["id"])

    return sorted(event_ids)


def _find_recent_suspicious_process_event_ids(*, host: str) -> list[int]:
    # Return the exact process-event IDs that currently form the suspicious burst window.
    settings = get_settings()

    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, ts, event_type, category, severity
            FROM events
            WHERE host = ?
            ORDER BY ts DESC
            """,
            (host,),
        )
        rows = cursor.fetchall()

    now = None
    window = timedelta(minutes=settings.suspicious_process_window_minutes)
    event_ids = []

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
            event_ids.append(row["id"])

    return sorted(event_ids)


def _create_alert(
    *,
    alert_type: str,
    severity: str,
    host: str,
    message: str,
    event_count: int,
    event_ids: list[int],
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
        for linked_event_id in event_ids:
            cursor.execute(
                """
                INSERT OR IGNORE INTO alert_events (alert_id, event_id)
                VALUES (?, ?)
                """,
                (alert["id"], linked_event_id),
            )

    alert["event_ids"] = event_ids
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


def _classify_critical_service(
    *, service_key: Optional[str], service_name: Optional[str]
) -> Optional[str]:
    normalized_key = (service_key or "").strip().lower()
    if normalized_key in {"windows_defender", "security_center"}:
        return normalized_key

    normalized_name = _normalize_text_for_matching(service_name)
    if any(alias in normalized_name for alias in ("windows defender", "microsoft defender", "защитник windows")):
        return "windows_defender"
    if any(alias in normalized_name for alias in ("security center", "turvakeskus", "центр обеспечения безопасности", "центр безопасности")):
        return "security_center"
    return None


def _service_label(service_key: str) -> str:
    if service_key == "windows_defender":
        return "Windows Defender"
    if service_key == "security_center":
        return "Security Center"
    return service_key


def _normalize_text_for_matching(value: Optional[str]) -> str:
    if not value:
        return ""
    return value.strip().lower().replace("ä", "a").replace("ö", "o")
