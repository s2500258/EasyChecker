from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..db import db_cursor
from ..config import get_settings


router = APIRouter(prefix="/rules", tags=["rules"])


class FailedLoginRuleOut(BaseModel):
    failed_login_threshold: int
    failed_login_window_minutes: int


class FailedLoginRuleUpdate(BaseModel):
    failed_login_threshold: int = Field(..., ge=2, le=20)
    failed_login_window_minutes: int = Field(..., ge=1, le=60)


class SuspiciousProcessRuleOut(BaseModel):
    suspicious_process_threshold: int
    suspicious_process_window_minutes: int


class SuspiciousProcessRuleUpdate(BaseModel):
    suspicious_process_threshold: int = Field(..., ge=2, le=20)
    suspicious_process_window_minutes: int = Field(..., ge=1, le=60)


@router.get("/failed-login", response_model=FailedLoginRuleOut)
def get_failed_login_rule() -> FailedLoginRuleOut:
    return FailedLoginRuleOut(**_load_failed_login_rule())


@router.put("/failed-login", response_model=FailedLoginRuleOut)
def update_failed_login_rule(payload: FailedLoginRuleUpdate) -> FailedLoginRuleOut:
    updates = {
        "failed_login_threshold": str(payload.failed_login_threshold),
        "failed_login_window_minutes": str(payload.failed_login_window_minutes),
    }

    _save_rule_updates(updates)

    return FailedLoginRuleOut(**_load_failed_login_rule())


@router.get("/suspicious-process", response_model=SuspiciousProcessRuleOut)
def get_suspicious_process_rule() -> SuspiciousProcessRuleOut:
    return SuspiciousProcessRuleOut(**_load_suspicious_process_rule())


@router.put("/suspicious-process", response_model=SuspiciousProcessRuleOut)
def update_suspicious_process_rule(
    payload: SuspiciousProcessRuleUpdate,
) -> SuspiciousProcessRuleOut:
    updates = {
        "suspicious_process_threshold": str(payload.suspicious_process_threshold),
        "suspicious_process_window_minutes": str(
            payload.suspicious_process_window_minutes
        ),
    }

    _save_rule_updates(updates)

    return SuspiciousProcessRuleOut(**_load_suspicious_process_rule())


def _load_failed_login_rule() -> dict[str, int]:
    settings = get_settings()
    values = {
        "failed_login_threshold": settings.failed_login_threshold,
        "failed_login_window_minutes": settings.failed_login_window_minutes,
    }

    return _load_rule_values(
        values,
        ("failed_login_threshold", "failed_login_window_minutes"),
    )


def _load_suspicious_process_rule() -> dict[str, int]:
    settings = get_settings()
    values = {
        "suspicious_process_threshold": settings.suspicious_process_threshold,
        "suspicious_process_window_minutes": settings.suspicious_process_window_minutes,
    }

    return _load_rule_values(
        values,
        ("suspicious_process_threshold", "suspicious_process_window_minutes"),
    )


def _load_rule_values(values: dict[str, int], keys: tuple[str, ...]) -> dict[str, int]:
    placeholders = ", ".join("?" for _ in keys)

    with db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT key, value
            FROM rule_settings
            WHERE key IN ({placeholders})
            """,
            keys,
        )
        rows = cursor.fetchall()

    for row in rows:
        values[row["key"]] = int(row["value"])

    return values


def _save_rule_updates(updates: dict[str, str]) -> None:
    with db_cursor(commit=True) as cursor:
        for key, value in updates.items():
            cursor.execute(
                """
                INSERT INTO rule_settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )
