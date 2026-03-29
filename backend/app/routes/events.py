from fastapi import APIRouter

from ..db import db_cursor
from ..schemas import EventOut
from ..utils import load_raw_data


router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventOut])
def list_events() -> list[EventOut]:
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id,
                ts,
                host,
                os_type,
                event_type,
                event_code,
                category,
                severity,
                username,
                ip_address,
                message,
                source,
                raw_data,
                created_at
            FROM events
            ORDER BY ts DESC, id DESC
            """
        )
        rows = cursor.fetchall()

    events = []
    for row in rows:
        event = dict(row)
        event["raw_data"] = load_raw_data(event["raw_data"])
        events.append(EventOut(**event))

    return events
