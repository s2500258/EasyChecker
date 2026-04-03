from typing import Optional
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from ..db import db_cursor
from ..schemas import HostOut


router = APIRouter(prefix="/hosts", tags=["hosts"])

SEVERITY_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
ONLINE_WINDOW = timedelta(minutes=2)


@router.get("", response_model=list[HostOut])
def list_hosts() -> list[HostOut]:
    # Build a lightweight host inventory from existing events and alerts
    # instead of introducing a separate hosts table at the MVP stage.
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT host, os_type, event_type, severity, ts
            FROM events
            ORDER BY ts DESC, id DESC
            """
        )
        event_rows = cursor.fetchall()

        cursor.execute(
            """
            SELECT host, severity
            FROM alerts
            """
        )
        alert_rows = cursor.fetchall()

    hosts: dict[str, dict] = {}

    for row in event_rows:
        host = row["host"]
        summary = hosts.setdefault(
            host,
            {
                "host": host,
                "os_type": row["os_type"],
                "last_seen": row["ts"],
                "activity_status": _activity_status(row["ts"]),
                "total_events": 0,
                "total_alerts": 0,
                "highest_severity": row["severity"],
                "last_event_type": row["event_type"],
            },
        )

        summary["total_events"] += 1
        if not summary["os_type"] and row["os_type"]:
            summary["os_type"] = row["os_type"]
        if row["ts"] and (
            not summary["last_seen"] or row["ts"] > summary["last_seen"]
        ):
            summary["last_seen"] = row["ts"]
            summary["activity_status"] = _activity_status(row["ts"])
        if _severity_rank(row["severity"]) > _severity_rank(summary["highest_severity"]):
            summary["highest_severity"] = row["severity"]

    for row in alert_rows:
        host = row["host"]
        summary = hosts.setdefault(
            host,
            {
                "host": host,
                "os_type": None,
                "last_seen": None,
                "activity_status": "OFFLINE",
                "total_events": 0,
                "total_alerts": 0,
                "highest_severity": row["severity"],
                "last_event_type": None,
            },
        )
        summary["total_alerts"] += 1
        if _severity_rank(row["severity"]) > _severity_rank(summary["highest_severity"]):
            summary["highest_severity"] = row["severity"]

    ordered_hosts = sorted(
        hosts.values(),
        key=lambda item: (
            item["last_seen"] or "",
            item["total_alerts"],
            item["host"].lower(),
        ),
        reverse=True,
    )

    return [HostOut(**host) for host in ordered_hosts]


def _severity_rank(value: Optional[str]) -> int:
    if not value:
        return 0
    return SEVERITY_ORDER.get(value.upper(), 0)


def _activity_status(last_seen: Optional[str]) -> str:
    if not last_seen:
        return "OFFLINE"

    try:
        seen_at = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
    except ValueError:
        return "OFFLINE"

    if seen_at.tzinfo is None:
        seen_at = seen_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    return "ONLINE" if now - seen_at <= ONLINE_WINDOW else "OFFLINE"
