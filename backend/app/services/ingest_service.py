from ..db import db_cursor
from ..schemas import EventIn
from ..utils import dump_raw_data, parse_event_timestamp, utc_now_iso
from .rules import evaluate_event_rules


def ingest_event(event: EventIn) -> dict:
    parse_event_timestamp(event.ts)

    payload = event.model_dump()
    payload["raw_data"] = dump_raw_data(payload["raw_data"])
    payload["created_at"] = utc_now_iso()

    with db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO events (
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
            )
            VALUES (
                :ts,
                :host,
                :os_type,
                :event_type,
                :event_code,
                :category,
                :severity,
                :username,
                :ip_address,
                :message,
                :source,
                :raw_data,
                :created_at
            )
            """,
            payload,
        )
        event_id = cursor.lastrowid

    stored_event = {"id": event_id, **payload}
    stored_event["raw_data"] = event.raw_data
    generated_alerts = evaluate_event_rules(
        host=event.host,
        message=event.message,
    )
    return {"event": stored_event, "alerts": generated_alerts}
