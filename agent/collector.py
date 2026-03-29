import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import xml.etree.ElementTree as ET

from config import get_settings
from sample_events import build_sample_events
from schemas import AgentEvent


STATE_FILE = Path(__file__).resolve().parent / ".collector_state.json"
WINDOWS_CHANNELS = {
    "Security": [4624, 4625, 4688],
    "System": [7036],
}
XML_NAMESPACE = {"evt": "http://schemas.microsoft.com/win/2004/08/events/event"}


def collect_events() -> list[AgentEvent]:
    settings = get_settings()

    if settings.event_source == "sample":
        events = build_sample_events(host=settings.hostname, os_type=settings.os_type)
        return events[: settings.max_events_per_cycle]

    if settings.event_source == "windows":
        events = collect_windows_events()
        return list(events)[: settings.max_events_per_cycle]

    raise ValueError(
        f"Unsupported EVENT_SOURCE '{settings.event_source}'. Use 'sample' or 'windows'."
    )


def collect_windows_events() -> list[AgentEvent]:
    settings = get_settings()
    state = _load_state()

    try:
        import win32evtlog  # type: ignore
    except ImportError:
        raise RuntimeError(
            "Windows Event Log support is unavailable. Install pywin32 and run on Windows."
        )

    try:
        raw_events = []
        for channel, event_ids in WINDOWS_CHANNELS.items():
            try:
                raw_events.extend(
                    _query_channel_events(
                        win32evtlog=win32evtlog,
                        channel=channel,
                        event_ids=event_ids,
                        last_record_id=state.get(channel, 0),
                    )
                )
            except Exception as exc:
                print(f"Windows collector could not read channel {channel}: {exc}")

        normalized_events = []
        latest_record_ids = dict(state)

        for raw_event in sorted(
            raw_events, key=lambda item: (item["timestamp"], item["record_id"])
        ):
            normalized = _normalize_windows_event(raw_event, settings.hostname)
            if normalized is None:
                continue
            normalized_events.append(normalized)
            latest_record_ids[raw_event["channel"]] = max(
                latest_record_ids.get(raw_event["channel"], 0), raw_event["record_id"]
            )

        if latest_record_ids != state:
            _save_state(latest_record_ids)

        if normalized_events:
            return normalized_events
        print("Windows collector found no usable live events in this cycle.")
        return []
    except Exception as exc:
        raise RuntimeError(f"Windows collector failed: {exc}") from exc


def _query_channel_events(
    *, win32evtlog, channel: str, event_ids: list[int], last_record_id: int
) -> list[dict[str, Any]]:
    query = _build_query(event_ids)
    flags = win32evtlog.EvtQueryChannelPath | win32evtlog.EvtQueryReverseDirection
    query_handle = win32evtlog.EvtQuery(channel, flags, query)
    raw_events = []

    try:
        while True:
            handles = win32evtlog.EvtNext(query_handle, 16)
            if not handles:
                break

            for handle in handles:
                try:
                    xml_payload = win32evtlog.EvtRender(
                        handle, win32evtlog.EvtRenderEventXml
                    )
                    parsed = _parse_event_xml(channel=channel, xml_payload=xml_payload)
                    if parsed["record_id"] <= last_record_id:
                        return raw_events
                    parsed["message"] = _format_event_message(
                        win32evtlog=win32evtlog,
                        event_handle=handle,
                        provider_name=parsed["provider"],
                    )
                    raw_events.append(parsed)
                finally:
                    _evt_close(win32evtlog, handle)
    finally:
        _evt_close(win32evtlog, query_handle)

    return raw_events


def _build_query(event_ids: list[int]) -> str:
    conditions = " or ".join(f"EventID={event_id}" for event_id in event_ids)
    return f"*[System[{conditions}]]"


def _parse_event_xml(*, channel: str, xml_payload: str) -> dict[str, Any]:
    root = ET.fromstring(xml_payload)
    system = root.find("evt:System", XML_NAMESPACE)
    event_data = root.find("evt:EventData", XML_NAMESPACE)

    provider = _find_attr(system, "evt:Provider", "Name")
    event_id = int(_find_text(system, "evt:EventID") or "0")
    record_id = int(_find_text(system, "evt:EventRecordID") or "0")
    computer = _find_text(system, "evt:Computer")
    timestamp = _find_attr(system, "evt:TimeCreated", "SystemTime")

    data_map = {}
    data_values = []
    if event_data is not None:
        for item in event_data.findall("evt:Data", XML_NAMESPACE):
            name = item.get("Name")
            text = (item.text or "").strip()
            if name:
                data_map[name] = text
            if text:
                data_values.append(text)

    return {
        "channel": channel,
        "provider": provider,
        "event_id": event_id,
        "record_id": record_id,
        "computer": computer,
        "timestamp": _normalize_timestamp(timestamp),
        "event_data": data_map,
        "event_values": data_values,
    }


def _normalize_windows_event(
    raw_event: dict[str, Any], fallback_host: str
) -> Optional[AgentEvent]:
    event_id = raw_event["event_id"]
    if event_id == 4625:
        return _normalize_failed_login(raw_event, fallback_host)
    if event_id == 4624:
        return _normalize_successful_login(raw_event, fallback_host)
    if event_id == 4688:
        return _normalize_process_created(raw_event, fallback_host)
    if event_id == 7036:
        return _normalize_service_change(raw_event, fallback_host)
    return None


def _normalize_failed_login(raw_event: dict[str, Any], fallback_host: str) -> AgentEvent:
    data = raw_event["event_data"]
    username = _pick_first(data, ["TargetUserName", "SubjectUserName"])
    ip_address = _clean_ip(_pick_first(data, ["IpAddress"]))
    logon_type = _pick_first(data, ["LogonType"])
    status = _pick_first(data, ["Status", "SubStatus"])

    return AgentEvent(
        ts=raw_event["timestamp"],
        host=raw_event["computer"] or fallback_host,
        os_type="windows",
        event_type="authentication",
        event_code="4625",
        category="login_failure",
        severity="MEDIUM",
        username=username,
        ip_address=ip_address,
        message=raw_event["message"] or "Failed login attempt",
        source="windows_event_log",
        raw_data={
            "provider": raw_event["provider"],
            "channel": raw_event["channel"],
            "record_id": raw_event["record_id"],
            "logon_type": logon_type,
            "status": status,
        },
    )


def _normalize_successful_login(
    raw_event: dict[str, Any], fallback_host: str
) -> AgentEvent:
    data = raw_event["event_data"]
    username = _pick_first(data, ["TargetUserName", "SubjectUserName"])
    ip_address = _clean_ip(_pick_first(data, ["IpAddress"]))
    logon_type = _pick_first(data, ["LogonType"])

    return AgentEvent(
        ts=raw_event["timestamp"],
        host=raw_event["computer"] or fallback_host,
        os_type="windows",
        event_type="authentication",
        event_code="4624",
        category="login_success",
        severity="LOW",
        username=username,
        ip_address=ip_address,
        message=raw_event["message"] or "Successful login",
        source="windows_event_log",
        raw_data={
            "provider": raw_event["provider"],
            "channel": raw_event["channel"],
            "record_id": raw_event["record_id"],
            "logon_type": logon_type,
        },
    )


def _normalize_process_created(
    raw_event: dict[str, Any], fallback_host: str
) -> AgentEvent:
    data = raw_event["event_data"]
    process_name = _pick_first(data, ["NewProcessName", "ProcessName"]) or "unknown"
    command_line = _pick_first(data, ["CommandLine"])
    parent_process = _pick_first(data, ["ParentProcessName", "CreatorProcessName"])
    username = _pick_first(data, ["SubjectUserName", "TargetUserName"])

    return AgentEvent(
        ts=raw_event["timestamp"],
        host=raw_event["computer"] or fallback_host,
        os_type="windows",
        event_type="process",
        event_code="4688",
        category="process_created",
        severity="MEDIUM",
        username=username,
        ip_address=None,
        message=raw_event["message"] or f"Process {process_name} was created",
        source="windows_event_log",
        raw_data={
            "provider": raw_event["provider"],
            "channel": raw_event["channel"],
            "record_id": raw_event["record_id"],
            "process_name": process_name,
            "command_line": command_line,
            "parent_process": parent_process,
        },
    )


def _normalize_service_change(raw_event: dict[str, Any], fallback_host: str) -> AgentEvent:
    service_name = _pick_first(raw_event["event_data"], ["param1", "ServiceName"])
    state = _pick_first(raw_event["event_data"], ["param2", "State"])

    if not service_name and raw_event["event_values"]:
        service_name = raw_event["event_values"][0]
    if not state and len(raw_event["event_values"]) > 1:
        state = raw_event["event_values"][1]

    state_normalized = (state or "").strip().lower()
    category = "service_stopped" if state_normalized == "stopped" else "service_state_change"
    severity = "HIGH" if category == "service_stopped" else "MEDIUM"
    default_message = (
        f"Service {service_name} stopped"
        if category == "service_stopped"
        else f"Service {service_name} changed state to {state}"
    )

    return AgentEvent(
        ts=raw_event["timestamp"],
        host=raw_event["computer"] or fallback_host,
        os_type="windows",
        event_type="system",
        event_code="7036",
        category=category,
        severity=severity,
        username=None,
        ip_address=None,
        message=raw_event["message"] or default_message,
        source="windows_event_log",
        raw_data={
            "provider": raw_event["provider"],
            "channel": raw_event["channel"],
            "record_id": raw_event["record_id"],
            "service_name": service_name,
            "state": state,
        },
    )


def _format_event_message(
    *, win32evtlog, event_handle, provider_name: Optional[str]
) -> str:
    if not provider_name:
        return ""

    publisher_handle = None
    try:
        publisher_handle = win32evtlog.EvtOpenPublisherMetadata(provider_name)
        return win32evtlog.EvtFormatMessage(
            publisher_handle,
            event_handle,
            win32evtlog.EvtFormatMessageEvent,
        ).strip()
    except Exception:
        return ""
    finally:
        if publisher_handle is not None:
            try:
                _evt_close(win32evtlog, publisher_handle)
            except Exception:
                pass


def _normalize_timestamp(value: Optional[str]) -> str:
    if not value:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _pick_first(values: dict[str, Any], keys: list[str]) -> Optional[str]:
    for key in keys:
        value = values.get(key)
        if value and value != "-":
            return value
    return None


def _clean_ip(value: Optional[str]) -> Optional[str]:
    if not value or value in {"-", "::1", "127.0.0.1"}:
        return None
    return value


def _find_text(parent, path: str) -> Optional[str]:
    if parent is None:
        return None
    node = parent.find(path, XML_NAMESPACE)
    if node is None or node.text is None:
        return None
    return node.text.strip()


def _find_attr(parent, path: str, attr_name: str) -> Optional[str]:
    if parent is None:
        return None
    node = parent.find(path, XML_NAMESPACE)
    if node is None:
        return None
    value = node.get(attr_name)
    if value is None:
        return None
    return value.strip()


def _load_state() -> dict[str, int]:
    if not STATE_FILE.exists():
        return {}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {str(key): int(value) for key, value in data.items()}


def _save_state(state: dict[str, int]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _evt_close(win32evtlog, handle) -> None:
    close_fn = getattr(win32evtlog, "EvtClose", None)
    if close_fn is None:
        return
    close_fn(handle)
