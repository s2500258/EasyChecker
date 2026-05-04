from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# Immutable snapshot returned to the console layer or UI layer.
@dataclass(frozen=True)
class AgentRuntimeSnapshot:
    started_at: str
    events_sent: int
    last_status: str
    last_error: str
    last_success_at: str
    last_event_summary: str
    is_running: bool
    cycle_count: int


# Shared runtime state for the worker thread and any presentation layer.
# The agent loop writes into this object while the console mode or GUI reads
# immutable snapshots from it without having to manage low-level locks itself.
class AgentRuntimeState:
    def __init__(self) -> None:
        self._lock = Lock()
        self._started_at = utc_now_iso()
        self._events_sent = 0
        self._last_status = "Starting"
        self._last_error = ""
        self._last_success_at = ""
        self._last_event_summary = ""
        self._is_running = False
        self._cycle_count = 0

    def snapshot(self) -> AgentRuntimeSnapshot:
        with self._lock:
            return AgentRuntimeSnapshot(
                started_at=self._started_at,
                events_sent=self._events_sent,
                last_status=self._last_status,
                last_error=self._last_error,
                last_success_at=self._last_success_at,
                last_event_summary=self._last_event_summary,
                is_running=self._is_running,
                cycle_count=self._cycle_count,
            )

    def mark_running(self, status: str) -> None:
        with self._lock:
            self._is_running = True
            self._last_status = status

    def mark_cycle_started(self) -> None:
        with self._lock:
            self._cycle_count += 1
            self._last_status = "Collecting events"

    def mark_no_events(self) -> None:
        with self._lock:
            self._last_status = "No events collected"
            self._last_event_summary = ""

    def mark_event_sent(self, *, summary: str) -> None:
        with self._lock:
            self._events_sent += 1
            self._last_status = "Last send ok"
            self._last_error = ""
            self._last_success_at = utc_now_iso()
            self._last_event_summary = summary

    def mark_error(self, message: str) -> None:
        with self._lock:
            self._last_status = "Error"
            self._last_error = message

    def mark_stopped(self, status: str) -> None:
        with self._lock:
            self._is_running = False
            self._last_status = status
