import csv
from io import StringIO
import os
import subprocess
from dataclasses import dataclass
from typing import Optional

from config import Settings

PROCESS_CREATION_SUBCATEGORY = "/subcategory:Process Creation"


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
        PROCESS_CREATION_SUBCATEGORY,
        "/r",
    )
    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip() or "unknown error"
        return ProcessAuditStatus(
            code="check-failed",
            message=f"Could not check Process Creation audit: {details}",
        )

    parsed_status = _parse_auditpol_csv_status(result.stdout)
    if parsed_status is not None:
        return parsed_status

    output = result.stdout.strip().lower()
    if _text_means_no_auditing(output):
        return ProcessAuditStatus(
            code="disabled",
            message="Process Creation audit is disabled.",
        )
    if _text_means_success_enabled(output):
        return ProcessAuditStatus(
            code="enabled",
            message="Process Creation audit is enabled.",
        )
    return ProcessAuditStatus(
        code="unknown",
        message="Process Creation audit status could not be parsed from auditpol output.",
    )


def _enable_process_creation_audit() -> ProcessAuditStatus:
    result = _run_auditpol(
        "auditpol",
        "/set",
        PROCESS_CREATION_SUBCATEGORY,
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


def _parse_auditpol_csv_status(output: str) -> Optional[ProcessAuditStatus]:
    rows = [row for row in csv.reader(StringIO(output)) if row]
    if len(rows) < 2:
        return None

    # Expected report format includes a header row and one data row whose last
    # columns describe inclusion/exclusion policy for the requested subcategory.
    data_row = rows[-1]
    if len(data_row) < 2:
        return None

    inclusion_setting = data_row[-2].strip().lower()
    exclusion_setting = data_row[-1].strip().lower()

    if _text_means_success_enabled(inclusion_setting):
        return ProcessAuditStatus(
            code="enabled",
            message="Process Creation audit is enabled.",
        )
    if _text_means_no_auditing(inclusion_setting) or _text_means_failure_only(
        inclusion_setting
    ):
        return ProcessAuditStatus(
            code="disabled",
            message="Process Creation audit is disabled.",
        )
    if exclusion_setting and _text_means_success_enabled(exclusion_setting):
        return ProcessAuditStatus(
            code="disabled",
            message="Process Creation audit is excluded by policy.",
        )
    return None


def _text_means_success_enabled(value: str) -> bool:
    normalized = _normalize_text(value)
    tokens = (
        "success",
        "success_and_failure",
        "failure_and_success",
        "uspeh",
        "uspeh_i_otkaz",
        "onnist",
        "onnistuminen",
    )
    return any(token in normalized for token in tokens)


def _text_means_failure_only(value: str) -> bool:
    normalized = _normalize_text(value)
    tokens = (
        "failure",
        "otkaz",
        "epaonn",
    )
    return any(token in normalized for token in tokens) and not _text_means_success_enabled(
        value
    )


def _text_means_no_auditing(value: str) -> bool:
    normalized = _normalize_text(value)
    tokens = (
        "no_auditing",
        "net_audita",
        "ei_valvontaa",
        "off",
        "none",
    )
    return any(token in normalized for token in tokens)


def _normalize_text(value: str) -> str:
    return (
        value.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("ё", "е")
        .replace("ä", "a")
        .replace("ö", "o")
        .replace("å", "a")
    )
