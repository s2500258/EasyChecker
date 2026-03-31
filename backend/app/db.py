import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .config import get_settings


def _ensure_db_directory() -> None:
    # Ensure the SQLite file can be created before opening a connection.
    db_path = get_settings().sqlite_db_path
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    # The MVP uses sqlite3 directly to keep the data layer lightweight.
    _ensure_db_directory()
    connection = sqlite3.connect(get_settings().sqlite_db_path)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def db_cursor(commit: bool = False) -> Iterator[sqlite3.Cursor]:
    # Centralize connection setup/teardown so callers only manage SQL statements.
    connection = get_connection()
    cursor = connection.cursor()
    try:
        yield cursor
        if commit:
            connection.commit()
    finally:
        cursor.close()
        connection.close()
