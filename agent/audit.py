import os
import subprocess
from dataclasses import dataclass

from config import Settings


@dataclass(frozen=True)
class ProcessAuditStatus:
    code: str
    message: str


# Startup helper for Windows process-creation auditing.
# The agent can check whether Event ID 4688 generation is enabled and, when the
# optional config flag is set, try to enable success auditing automatically.
def ensure_process_creation_audit(settings: Settings) -> ProcessAuditStatus:
    if settings.event_source.strip().lower() != "windows":
        return ProcessAuditStatus(
            code="not-needed",
            message="Process audit check skipped outside Windows live mode.",
        )
    if not settings.collect_process_events:
        return ProcessAuditStatus(
            code="not-needed",
            message="Process audit check skipped because process collection is disabled.",
        )
    if os.name != "nt":
        return ProcessAuditStatus(
            code="not-supported",
            message="Process audit check is only supported on Windows.",
        )

    current_status = _query_process_creation_audit()
    if current_status.code == "enabled":
        return current_status
    if current_status.code != "disabled":
        return current_status
    if not settings.auto_enable_process_audit:
        return ProcessAuditStatus(
            code="disabled",
            message=(
                "Process Creation audit is disabled. "
                "Set AUTO_ENABLE_PROCESS_AUDIT=true and run as administrator to enable it automatically."
            ),
        )

    enable_status = _enable_process_creation_audit()
    if enable_status.code == "enabled":
        return ProcessAuditStatus(
            code="enabled",
            message="Process Creation audit was enabled automatically.",
        )
    return enable_status


def _query_process_creation_audit() -> ProcessAuditStatus:
    result = _run_auditpol(
        "auditpol",
        "/get",
        '/subcategory:"Process Creation"',
    )
    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip() or "unknown error"
        return ProcessAuditStatus(
            code="check-failed",
            message=f"Could not check Process Creation audit: {details}",
        )

    output = result.stdout.strip().lower()
    if "no auditing" in output:
        return ProcessAuditStatus(
            code="disabled",
            message="Process Creation audit is disabled.",
        )
    if "success" in output:
        return ProcessAuditStatus(
            code="enabled",
            message="Process Creation audit is enabled.",
        )
    return ProcessAuditStatus(
        code="unknown",
        message="Process Creation audit status could not be parsed.",
    )


def _enable_process_creation_audit() -> ProcessAuditStatus:
    result = _run_auditpol(
        "auditpol",
        "/set",
        '/subcategory:"Process Creation"',
        "/success:enable",
    )
    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip() or "unknown error"
        return ProcessAuditStatus(
            code="enable-failed",
            message=(
                "Auto-enable of Process Creation audit failed. "
                f"Administrator rights may be required: {details}"
            ),
        )

    refreshed = _query_process_creation_audit()
    if refreshed.code == "enabled":
        return refreshed
    return ProcessAuditStatus(
        code="enable-failed",
        message="Auto-enable command completed, but Process Creation audit still appears disabled.",
    )


def _run_auditpol(*command_parts: str) -> subprocess.CompletedProcess:
    run_kwargs = {
        "capture_output": True,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "check": False,
    }
    if os.name == "nt":
        run_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.run(list(command_parts), **run_kwargs)
