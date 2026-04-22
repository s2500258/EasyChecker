from datetime import datetime, timedelta, timezone
from typing import Optional

from schemas import AgentEvent


# Deterministic sample events used for safe connectivity testing and local demos.
def build_sample_events(
    *, host: str, host_ip: Optional[str], os_type: str
) -> list[AgentEvent]:
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    return [
        AgentEvent(
            ts=timestamp,
            host=host,
            host_ip=host_ip,
            os_type=os_type,
            event_type="authentication",
            event_code="4625",
            category="login_failure",
            severity="MEDIUM",
            username="student",
            ip_address="192.168.1.50",
            message="Failed login attempt",
            source="agent_sample",
            raw_data={
                "provider": "Security",
                "logon_type": 3,
                "status": "0xC000006D",
            },
        ),
        AgentEvent(
            ts=timestamp,
            host=host,
            host_ip=host_ip,
            os_type=os_type,
            event_type="authentication",
            event_code="4624",
            category="login_success",
            severity="LOW",
            username="student",
            ip_address="192.168.1.50",
            message="Successful login",
            source="agent_sample",
            raw_data={
                "provider": "Security",
                "logon_type": 2,
            },
        ),
        AgentEvent(
            ts=timestamp,
            host=host,
            host_ip=host_ip,
            os_type=os_type,
            event_type="process",
            event_code="4688",
            category="process_created",
            severity="MEDIUM",
            username="student",
            ip_address=None,
            message="Process powershell.exe was created",
            source="agent_sample",
            raw_data={
                "provider": "Security",
                "process_name": "powershell.exe",
                "parent_process": "explorer.exe",
                "command_line": "powershell.exe -ExecutionPolicy Bypass",
            },
        ),
        AgentEvent(
            ts=timestamp,
            host=host,
            host_ip=host_ip,
            os_type=os_type,
            event_type="system",
            event_code="7036",
            category="service_state_change",
            severity="MEDIUM",
            username=None,
            ip_address=None,
            message="Windows service entered a running state",
            source="agent_sample",
            raw_data={
                "provider": "Service Control Manager",
                "service_name": "Windows Update",
                "state": "running",
            },
        ),
        AgentEvent(
            ts=timestamp,
            host=host,
            host_ip=host_ip,
            os_type=os_type,
            event_type="system",
            event_code="7036",
            category="service_stopped",
            severity="HIGH",
            username=None,
            ip_address=None,
            message="Windows Defender service stopped",
            source="agent_sample",
            raw_data={
                "provider": "Service Control Manager",
                "service_name": "Windows Defender",
                "state": "stopped",
            },
        ),
    ]


# Multi-host sample data used when the project needs to simulate a small fleet
# with distinct incident patterns across multiple machines.
def build_fleet_sample_events() -> list[AgentEvent]:
    fleet = [
        {
            "agent_id": "agent-win-01",
            "host": "WIN-PC-01",
            "host_ip": "192.168.1.101",
            "username": "student",
            "ip_address": "192.168.1.50",
            "pattern": "brute_force",
        },
        {
            "agent_id": "agent-win-02",
            "host": "WIN-LAB-02",
            "host_ip": "192.168.1.102",
            "username": "analyst",
            "ip_address": "192.168.1.51",
            "pattern": "suspicious_processes",
        },
        {
            "agent_id": "agent-win-03",
            "host": "WIN-OPS-03",
            "host_ip": "192.168.1.103",
            "username": "operator",
            "ip_address": "192.168.1.52",
            "pattern": "service_disruption",
        },
    ]

    events = []
    base_time = datetime.now(timezone.utc)

    for agent_index, agent in enumerate(fleet):
        for index in range(10):
            timestamp = (
                base_time - timedelta(minutes=4, seconds=59 - (agent_index * 10 + index))
            ).isoformat().replace("+00:00", "Z")
            events.append(
                _build_agent_event(
                    pattern=agent["pattern"],
                    index=index,
                    timestamp=timestamp,
                    agent_id=agent["agent_id"],
                    host=agent["host"],
                    host_ip=agent["host_ip"],
                    username=agent["username"],
                    ip_address=agent["ip_address"],
                )
            )

    return events


def _build_agent_event(
    *,
    pattern: str,
    index: int,
    timestamp: str,
    agent_id: str,
    host: str,
    host_ip: str,
    username: str,
    ip_address: str,
) -> AgentEvent:
    source = f"sample_fleet::{agent_id}"

    if pattern == "brute_force":
        if index < 6:
            return AgentEvent(
                ts=timestamp,
                host=host,
                host_ip=host_ip,
                os_type="windows",
                event_type="authentication",
                event_code="4625",
                category="login_failure",
                severity="MEDIUM",
                username=username,
                ip_address=ip_address,
                message=f"Failed login attempt for {username}",
                source=source,
                raw_data={
                    "provider": "Security",
                    "logon_type": 3,
                    "status": "0xC000006D",
                    "attempt_number": index + 1,
                },
            )

        return AgentEvent(
            ts=timestamp,
            host=host,
            host_ip=host_ip,
            os_type="windows",
            event_type="authentication",
            event_code="4624",
            category="login_success",
            severity="LOW",
            username=username,
            ip_address=ip_address,
            message=f"Successful login for {username}",
            source=source,
            raw_data={
                "provider": "Security",
                "logon_type": 2,
                "followed_failed_attempts": 6,
            },
        )

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
            return AgentEvent(
                ts=timestamp,
                host=host,
                host_ip=host_ip,
                os_type="windows",
                event_type="authentication",
                event_code=event_code,
                category=category,
                severity=severity,
                username=username,
                ip_address=ip_address,
                message=f"Successful login for {username}",
                source=source,
                raw_data={"provider": "Security", "logon_type": 2},
            )

        return AgentEvent(
            ts=timestamp,
            host=host,
            host_ip=host_ip,
            os_type="windows",
            event_type="process",
            event_code=event_code,
            category=category,
            severity=severity,
            username=username,
            ip_address=None,
            message=f"Process {process_name} was created",
            source=source,
            raw_data={
                "provider": "Security",
                "process_name": process_name,
                "parent_process": "explorer.exe",
                "command_line": command_line,
            },
        )

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

    return AgentEvent(
        ts=timestamp,
        host=host,
        host_ip=host_ip,
        os_type="windows",
        event_type="system",
        event_code=event_code,
        category=category,
        severity=severity,
        username=None,
        ip_address=None,
        message=message,
        source=source,
        raw_data={
            "provider": "Service Control Manager",
            "service_name": service_name,
            "state": state,
        },
    )
