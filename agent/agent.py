import time

from collector import collect_events, get_state_file_path
from config import get_env_file_path, get_runtime_dir, get_settings
from sender import send_event


# Main entry point for the agent.
# This module coordinates the high-level loop: load settings, collect events,
# send them to the backend, and sleep between cycles when needed.
def run_agent() -> None:
    settings = get_settings()
    print(
        "EasyChecker agent started "
        f"(source={settings.event_source}, host={settings.hostname}, "
        f"interval={settings.poll_interval}s, run_once={settings.run_once})"
    )
    # Print runtime paths explicitly so packaged Windows builds are easier to
    # diagnose when `.env` or state persistence does not behave as expected.
    print(f"Runtime directory: {get_runtime_dir()}")
    print(f"Env file: {get_env_file_path()}")
    print(f"State file: {get_state_file_path()}")

    while True:
        try:
            # Collect a batch of normalized events from the configured source.
            events = collect_events()
            if not events:
                print("No events collected in this cycle.")

            # Send events one by one so a single bad event does not block the batch.
            for event in events:
                result = send_event(event)
                alert_count = len(result.get("alerts", []))
                print(
                    f"Sent event {event.event_type}/{event.category} "
                    f"severity={event.severity} alerts={alert_count}"
                )
        except KeyboardInterrupt:
            print("Agent stopped by user.")
            break
        except Exception as exc:
            print(f"Agent cycle failed: {exc}")

        # In one-shot mode the agent exits after a single collection/send cycle.
        if settings.run_once:
            print("Agent finished one cycle and is exiting.")
            break

        time.sleep(settings.poll_interval)


if __name__ == "__main__":
    run_agent()
