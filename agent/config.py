import socket
from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path
import sys
import tempfile
from typing import Optional
from urllib.parse import urlparse


SOURCE_DIR = Path(__file__).resolve().parent


def get_runtime_dir() -> Path:
    # When the agent is bundled as an executable, use the executable directory
    # as the runtime base so `.env` and other writable files can live next to it.
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return SOURCE_DIR


def get_env_file_path() -> Path:
    # Keep configuration next to the source files in development and next to
    # the executable in packaged Windows builds.
    return get_runtime_dir() / ".env"


def get_state_dir() -> Path:
    # Prefer storing runtime state next to the executable for portability, but
    # fall back to a guaranteed user-writable location on Windows when the
    # executable directory cannot be written to.
    runtime_dir = get_runtime_dir()
    if _is_writable_dir(runtime_dir):
        return runtime_dir

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        fallback_dir = Path(local_app_data) / "EasyCheckerAgent"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        return fallback_dir

    return runtime_dir


# Centralized runtime settings for the agent.
# Values come from agent/.env first and fall back to OS environment variables
# or hardcoded defaults when no local override is present.
@dataclass(frozen=True)
class Settings:
    backend_url: str
    poll_interval: int
    hostname: str
    host_ip: Optional[str]
    os_type: str
    event_source: str
    max_events_per_cycle: int
    run_once: bool
    collect_login_events: bool
    collect_process_events: bool
    collect_service_events: bool
    process_name_allowlist: list[str]
    service_name_allowlist: list[str]


@lru_cache
def get_settings() -> Settings:
    # Cache settings so every module in the current process uses the same values.
    env_values = _load_env_file(get_env_file_path())
    backend_url = env_values.get(
        "BACKEND_URL", "http://127.0.0.1:8000/api/v1/ingest"
    )
    return Settings(
        backend_url=backend_url,
        poll_interval=int(env_values.get("POLL_INTERVAL", "5")),
        hostname=env_values.get("HOSTNAME", socket.gethostname()),
        host_ip=env_values.get("HOST_IP") or _detect_host_ip(backend_url),
        os_type=env_values.get("OS_TYPE", "windows"),
        event_source=env_values.get("EVENT_SOURCE", "sample"),
        max_events_per_cycle=int(env_values.get("MAX_EVENTS_PER_CYCLE", "3")),
        run_once=_parse_bool(env_values.get("RUN_ONCE", "false")),
        collect_login_events=_parse_bool(
            env_values.get("COLLECT_LOGIN_EVENTS", "true")
        ),
        collect_process_events=_parse_bool(
            env_values.get("COLLECT_PROCESS_EVENTS", "true")
        ),
        collect_service_events=_parse_bool(
            env_values.get("COLLECT_SERVICE_EVENTS", "true")
        ),
        process_name_allowlist=_parse_csv(
            env_values.get("PROCESS_NAME_ALLOWLIST", "")
        ),
        service_name_allowlist=_parse_csv(
            env_values.get("SERVICE_NAME_ALLOWLIST", "")
        ),
    )


def _load_env_file(path: Path) -> dict[str, str]:
    # Start with the real process environment, then override from the local .env file.
    values = dict(os.environ)
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()

    return values


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_csv(value: str) -> list[str]:
    # Parse comma-separated names from `.env` and normalize them so collector
    # filtering can do simple case-insensitive comparisons.
    return [
        item.strip().lower()
        for item in value.split(",")
        if item.strip()
    ]


def _is_writable_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path, delete=True):
            pass
        return True
    except OSError:
        return False


def _detect_host_ip(backend_url: str) -> Optional[str]:
    # Resolve the machine's host IP without requiring internet access.
    # We first try the backend host because it is the most relevant route in
    # real deployments, then fall back to a generic public resolver, and
    # finally inspect local hostname resolution as a last resort.
    backend_host = urlparse(backend_url).hostname
    candidates = [backend_host, "8.8.8.8"]

    for target in candidates:
        address = _probe_outbound_ip(target)
        if address:
            return address

    for address in _hostname_ip_candidates():
        if _is_usable_ipv4(address):
            return address

    return None


def _probe_outbound_ip(target: Optional[str]) -> Optional[str]:
    if not target:
        return None

    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect((target, 80))
        address = probe.getsockname()[0]
        return address if _is_usable_ipv4(address) else None
    except OSError:
        return None
    finally:
        probe.close()


def _hostname_ip_candidates() -> list[str]:
    addresses: list[str] = []

    try:
        hostname = socket.gethostname()
        addresses.extend(socket.gethostbyname_ex(hostname)[2])
    except OSError:
        pass

    try:
        for result in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            candidate = result[4][0]
            if candidate not in addresses:
                addresses.append(candidate)
    except OSError:
        pass

    return addresses


def _is_usable_ipv4(address: Optional[str]) -> bool:
    if not address:
        return False
    if address.startswith("127.") or address == "0.0.0.0":
        return False
    return True
