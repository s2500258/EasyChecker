from threading import Event
from time import sleep
from typing import Callable, Optional

from audit import ensure_process_creation_audit
from collector import collect_events, get_state_file_path
from config import get_env_file_path, get_runtime_dir, get_settings
from runtime_state import AgentRuntimeState
from sender import send_event


# Shared worker loop used by both console mode and GUI mode.
# The loop owns collection and sending, while callers decide how to surface
# progress updates through the optional log callback and runtime state object.
def run_agent_loop(
    *,
    state: AgentRuntimeState,
    stop_event: Event,
    log: Optional[Callable[[str], None]] = None,
) -> None:
    # Snapshot settings once for this worker instance. UI-triggered restarts
    # create a brand-new worker so each run still picks up fresh .env values.
    settings = get_settings()
    emit = log or (lambda message: None)

    state.mark_running("Running")
    emit(
        "EasyChecker agent started "
        f"(source={settings.event_source}, host={settings.hostname}, "
        f"interval={settings.poll_interval}s, run_once={settings.run_once})"
    )
    emit(f"Detected host IP: {settings.host_ip or 'N/A'}")
    emit(f"Runtime directory: {get_runtime_dir()}")
    emit(f"Env file: {get_env_file_path()}")
    emit(f"State file: {get_state_file_path()}")
    # Check Process Creation auditing once at startup rather than every poll
    # cycle, because the audit policy itself is not event data and rarely changes.
    process_audit_status = ensure_process_creation_audit(settings)
    state.mark_process_audit_status(process_audit_status.message)
    emit(process_audit_status.message)

    try:
        while not stop_event.is_set():
            try:
                state.mark_cycle_started()
                # Collect a batch of normalized events from the configured source.
                events = collect_events()
                if not events:
                    emit("No events collected in this cycle.")
                    state.mark_no_events()

                # Send events one by one so a single bad event does not block the batch.
                for event in events:
                    if stop_event.is_set():
                        break
                    result = send_event(event)
                    # Keep the operator-facing summary short and stable so the
                    # GUI can display the last sent event without overflowing.
                    alert_count = len(result.get("alerts", []))
                    summary = (
                        f"{event.event_type}/{event.category} "
                        f"severity={event.severity} alerts={alert_count}"
                    )
                    emit(f"Sent event {summary}")
                    state.mark_event_sent(summary=summary)
            except KeyboardInterrupt:
                emit("Agent stopped by user.")
                state.mark_stopped("Stopped by user")
                return
            except Exception as exc:
                error_message = f"Agent cycle failed: {exc}"
                emit(error_message)
                state.mark_error(str(exc))

            # In one-shot mode the agent exits after a single collection/send cycle.
            if settings.run_once:
                emit("Agent finished one cycle and is exiting.")
                state.mark_stopped("Finished one cycle")
                return

            _sleep_with_stop(settings.poll_interval, stop_event)
    finally:
        if not state.snapshot().is_running:
            return
        state.mark_stopped("Stopped")


def _sleep_with_stop(seconds: int, stop_event: Event) -> None:
    # Wake up in small increments so GUI exit requests do not have to wait for
    # the full poll interval before the worker thread can stop.
    remaining = max(0, seconds)
    while remaining > 0 and not stop_event.is_set():
        sleep(min(0.2, remaining))
        remaining -= 0.2
