import socket
from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path
import sys


SOURCE_DIR = Path(__file__).resolve().parent


def get_runtime_dir() -> Path:
    # When the agent is bundled as an executable, use the executable directory
    # as the runtime base so `.env` and other writable files can live next to it.
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return SOURCE_DIR


# Centralized runtime settings for the agent.
# Values come from agent/.env first and fall back to OS environment variables
# or hardcoded defaults when no local override is present.
@dataclass(frozen=True)
class Settings:
    backend_url: str
    poll_interval: int
    hostname: str
    os_type: str
    event_source: str
    max_events_per_cycle: int
    run_once: bool


@lru_cache
def get_settings() -> Settings:
    # Cache settings so every module in the current process uses the same values.
    env_values = _load_env_file(get_runtime_dir() / ".env")
    return Settings(
        backend_url=env_values.get(
            "BACKEND_URL", "http://127.0.0.1:8000/api/v1/ingest"
        ),
        poll_interval=int(env_values.get("POLL_INTERVAL", "5")),
        hostname=env_values.get("HOSTNAME", socket.gethostname()),
        os_type=env_values.get("OS_TYPE", "windows"),
        event_source=env_values.get("EVENT_SOURCE", "sample"),
        max_events_per_cycle=int(env_values.get("MAX_EVENTS_PER_CYCLE", "3")),
        run_once=_parse_bool(env_values.get("RUN_ONCE", "false")),
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
