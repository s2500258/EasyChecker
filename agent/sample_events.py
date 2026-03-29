from datetime import datetime, timezone

from schemas import AgentEvent


def build_sample_events(*, host: str, os_type: str) -> list[AgentEvent]:
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    return [
        AgentEvent(
            ts=timestamp,
            host=host,
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
