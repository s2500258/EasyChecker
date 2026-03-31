from datetime import timedelta

from ..config import get_settings
from ..db import db_cursor
from ..utils import parse_event_timestamp, utc_now_iso


def evaluate_event_rules(*, host: str, message: str) -> list[dict]:
    # The MVP rule focuses on repeated failed logins from the same host.
    settings = get_settings()
    if "failed login" not in message.lower():
        return []

    latest_matches = _count_recent_failed_logins(host=host)
    if latest_matches != settings.failed_login_threshold:
        return []

    # Create the alert only when the threshold is first reached in the window.
    alert = {
        "type": "Brute force attempt",
        "severity": "HIGH",
        "host": host,
        "message": (
            f"{latest_matches} failed logins detected from {host} "
            f"within {settings.failed_login_window_minutes} minutes."
        ),
        "created_at": utc_now_iso(),
        "event_count": latest_matches,
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

    return [alert]


def _count_recent_failed_logins(*, host: str) -> int:
    # Count failures relative to the newest relevant event for the host.
    settings = get_settings()

    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT ts, message
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
        if "failed login" not in row["message"].lower():
            continue

        event_time = parse_event_timestamp(row["ts"])
        if now is None:
            now = event_time

        if now - event_time <= window:
            count += 1

    return count
