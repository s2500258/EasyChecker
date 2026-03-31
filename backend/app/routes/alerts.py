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
        rows = cursor.fetchall()

    return [AlertOut(**dict(row)) for row in rows]
