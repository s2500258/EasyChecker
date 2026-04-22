from ..db import db_cursor
from ..schemas import EventIn
from ..utils import dump_raw_data, parse_event_timestamp, utc_now_iso
from .rules import evaluate_event_rules


def ingest_event(event: EventIn) -> dict:
    # Validate the event timestamp before anything is written to the database.
    parse_event_timestamp(event.ts)

    payload = event.model_dump()
    # raw_data stays flexible in Python but is stored as JSON text in SQLite.
    payload["raw_data"] = dump_raw_data(payload["raw_data"])
    payload["created_at"] = utc_now_iso()

    with db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO events (
                ts,
                host,
                host_ip,
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
                :host_ip,
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

    # Keep a response-friendly copy of the event without raw JSON text.
    stored_event = {"id": event_id, **payload}
    stored_event["raw_data"] = event.raw_data
    generated_alerts = evaluate_event_rules(
        host=event.host,
        event_type=event.event_type,
        category=event.category,
        severity=event.severity,
        message=event.message,
        raw_data=event.raw_data,
    )
    return {"event": stored_event, "alerts": generated_alerts}
