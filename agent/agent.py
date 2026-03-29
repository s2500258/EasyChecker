import time

from collector import collect_events
from config import get_settings
from sender import send_event


def run_agent() -> None:
    settings = get_settings()
    print(
        "EasyChecker agent started "
        f"(source={settings.event_source}, host={settings.hostname}, "
        f"interval={settings.poll_interval}s, run_once={settings.run_once})"
    )

    while True:
        try:
            events = collect_events()
            if not events:
                print("No events collected in this cycle.")
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

        if settings.run_once:
            print("Agent finished one cycle and is exiting.")
            break

        time.sleep(settings.poll_interval)


if __name__ == "__main__":
    run_agent()
