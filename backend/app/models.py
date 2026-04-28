from .db import db_cursor


def init_db() -> None:
    # Create the MVP tables and backfill any newer event columns.
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                host TEXT NOT NULL,
                host_ip TEXT,
                os_type TEXT,
                event_type TEXT NOT NULL,
                event_code TEXT,
                category TEXT,
                severity TEXT NOT NULL,
                username TEXT,
                ip_address TEXT,
                message TEXT NOT NULL,
                source TEXT,
                raw_data TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                severity TEXT NOT NULL,
                host TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL,
                event_count INTEGER NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS alert_events (
                alert_id INTEGER NOT NULL,
                event_id INTEGER NOT NULL,
                PRIMARY KEY (alert_id, event_id),
                FOREIGN KEY (alert_id) REFERENCES alerts(id),
                FOREIGN KEY (event_id) REFERENCES events(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rule_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        _seed_rule_settings(cursor)
        _ensure_event_columns(cursor)


def _ensure_event_columns(cursor) -> None:
    # Older local databases may miss fields added after the first schema version.
    cursor.execute("PRAGMA table_info(events)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    expected_columns = {
        "host_ip": "TEXT",
        "os_type": "TEXT",
        "event_code": "TEXT",
        "category": "TEXT",
        "username": "TEXT",
        "ip_address": "TEXT",
        "raw_data": "TEXT",
    }

    for column_name, column_type in expected_columns.items():
        if column_name not in existing_columns:
            cursor.execute(f"ALTER TABLE events ADD COLUMN {column_name} {column_type}")


def _seed_rule_settings(cursor) -> None:
    from .config import get_settings

    settings = get_settings()
    defaults = {
        "failed_login_threshold": str(settings.failed_login_threshold),
        "failed_login_window_minutes": str(settings.failed_login_window_minutes),
        "suspicious_process_threshold": str(settings.suspicious_process_threshold),
        "suspicious_process_window_minutes": str(settings.suspicious_process_window_minutes),
    }

    for key, value in defaults.items():
        cursor.execute(
            """
            INSERT OR IGNORE INTO rule_settings (key, value)
            VALUES (?, ?)
            """,
            (key, value),
        )
