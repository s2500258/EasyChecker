import json
from datetime import datetime, timedelta, timezone
from urllib import request


API_URL = "http://127.0.0.1:8000/api/v1/ingest"

AGENTS = [
    {
        "agent_id": "agent-win-01",
        "host": "WIN-PC-01",
        "username": "student",
        "ip_address": "192.168.1.50",
        "pattern": "brute_force",
    },
    {
        "agent_id": "agent-win-02",
        "host": "WIN-LAB-02",
        "username": "analyst",
        "ip_address": "192.168.1.51",
        "pattern": "suspicious_processes",
    },
    {
        "agent_id": "agent-win-03",
        "host": "WIN-OPS-03",
        "username": "operator",
        "ip_address": "192.168.1.52",
        "pattern": "service_disruption",
    },
]


def send_event(payload: dict) -> None:
    req = request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req) as response:
        print(response.read().decode("utf-8"))


def build_simulation_events() -> list[dict]:
    events = []
    base_time = datetime.now(timezone.utc)

    for agent_index, agent in enumerate(AGENTS):
        for event_index in range(10):
            ts = (
                base_time - timedelta(minutes=4, seconds=59 - (agent_index * 10 + event_index))
            ).isoformat().replace("+00:00", "Z")
            events.append(
                _build_event_payload(
                    pattern=agent["pattern"],
                    index=event_index,
                    ts=ts,
                    agent_id=agent["agent_id"],
                    host=agent["host"],
                    username=agent["username"],
                    ip_address=agent["ip_address"],
                )
            )

    return events


def _build_event_payload(
    *,
    pattern: str,
    index: int,
    ts: str,
    agent_id: str,
    host: str,
    username: str,
    ip_address: str,
) -> dict:
    source = f"manual_test::{agent_id}"

    if pattern == "brute_force":
        if index < 6:
            return {
                "ts": ts,
                "host": host,
                "os_type": "windows",
                "event_type": "authentication",
                "event_code": "4625",
                "category": "login_failure",
                "severity": "MEDIUM",
                "username": username,
                "ip_address": ip_address,
                "message": f"Failed login attempt for {username}",
                "source": source,
                "raw_data": {
                    "provider": "Security",
                    "logon_type": 3,
                    "status": "0xC000006D",
                    "attempt_number": index + 1,
                },
            }

        return {
            "ts": ts,
            "host": host,
            "os_type": "windows",
            "event_type": "authentication",
            "event_code": "4624",
            "category": "login_success",
            "severity": "LOW",
            "username": username,
            "ip_address": ip_address,
            "message": f"Successful login for {username}",
            "source": source,
            "raw_data": {
                "provider": "Security",
                "logon_type": 2,
                "followed_failed_attempts": 6,
            },
        }

    if pattern == "suspicious_processes":
        process_sequence = [
            ("4688", "process_created", "MEDIUM", "cmd.exe", "cmd.exe /c whoami"),
            ("4688", "process_created", "MEDIUM", "powershell.exe", "powershell.exe -nop"),
            ("4688", "process_created", "HIGH", "powershell.exe", "powershell.exe -ExecutionPolicy Bypass"),
            ("4688", "process_created", "HIGH", "rundll32.exe", "rundll32.exe javascript.dll,Start"),
            ("4688", "process_created", "HIGH", "wmic.exe", "wmic process call create powershell.exe"),
            ("4688", "process_created", "HIGH", "powershell.exe", "powershell.exe Invoke-WebRequest http://intranet"),
            ("4688", "process_created", "MEDIUM", "certutil.exe", "certutil.exe -urlcache -split -f file.exe"),
            ("4688", "process_created", "MEDIUM", "cmd.exe", "cmd.exe /c net user"),
            ("4624", "login_success", "LOW", "explorer.exe", None),
            ("4688", "process_created", "HIGH", "powershell.exe", "powershell.exe Get-Process"),
        ]
        event_code, category, severity, process_name, command_line = process_sequence[index]

        if category == "login_success":
            return {
                "ts": ts,
                "host": host,
                "os_type": "windows",
                "event_type": "authentication",
                "event_code": event_code,
                "category": category,
                "severity": severity,
                "username": username,
                "ip_address": ip_address,
                "message": f"Successful login for {username}",
                "source": source,
                "raw_data": {
                    "provider": "Security",
                    "logon_type": 2,
                },
            }

        return {
            "ts": ts,
            "host": host,
            "os_type": "windows",
            "event_type": "process",
            "event_code": event_code,
            "category": category,
            "severity": severity,
            "username": username,
            "ip_address": None,
            "message": f"Process {process_name} was created",
            "source": source,
            "raw_data": {
                "provider": "Security",
                "process_name": process_name,
                "parent_process": "explorer.exe",
                "command_line": command_line,
            },
        }

    service_sequence = [
        ("7036", "service_state_change", "MEDIUM", "Windows Update", "running"),
        ("7036", "service_state_change", "MEDIUM", "Windows Update", "stopped"),
        ("7036", "service_stopped", "HIGH", "Windows Defender", "stopped"),
        ("7036", "service_state_change", "MEDIUM", "Windows Defender", "starting"),
        ("7036", "service_state_change", "MEDIUM", "Windows Defender", "running"),
        ("7036", "service_stopped", "HIGH", "Security Center", "stopped"),
        ("7036", "service_state_change", "MEDIUM", "Security Center", "starting"),
        ("7036", "service_state_change", "MEDIUM", "Security Center", "running"),
        ("7036", "service_state_change", "MEDIUM", "Print Spooler", "stopped"),
        ("7036", "service_state_change", "MEDIUM", "Print Spooler", "running"),
    ]
    event_code, category, severity, service_name, state = service_sequence[index]
    message = (
        f"{service_name} service stopped"
        if category == "service_stopped"
        else f"{service_name} service changed state to {state}"
    )

    return {
        "ts": ts,
        "host": host,
        "os_type": "windows",
        "event_type": "system",
        "event_code": event_code,
        "category": category,
        "severity": severity,
        "username": None,
        "ip_address": None,
        "message": message,
        "source": source,
        "raw_data": {
            "provider": "Service Control Manager",
            "service_name": service_name,
            "state": state,
        },
    }


if __name__ == "__main__":
    for event in build_simulation_events():
        send_event(event)
