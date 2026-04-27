from fastapi import APIRouter

from ..db import db_cursor
from ..schemas import AlertOut


# Read-only alerts endpoint for generated rule hits.
router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts() -> list[AlertOut]:
    # Return newest alerts first for dashboards and alert review pages.
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, type, severity, host, message, created_at, event_count
            FROM alerts
            ORDER BY created_at DESC, id DESC
            """
        )
        alert_rows = cursor.fetchall()

        cursor.execute(
            """
            SELECT alert_id, event_id
            FROM alert_events
            ORDER BY alert_id DESC, event_id ASC
            """
        )
        link_rows = cursor.fetchall()

    event_ids_by_alert: dict[int, list[int]] = {}
    for row in link_rows:
        event_ids_by_alert.setdefault(row["alert_id"], []).append(row["event_id"])

    alerts = []
    for row in alert_rows:
        alert = dict(row)
        alert["event_ids"] = event_ids_by_alert.get(alert["id"], [])
        alerts.append(AlertOut(**alert))

    return alerts
