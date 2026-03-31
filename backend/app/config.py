from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent.parent


# Centralized backend configuration loaded from backend/.env.
class Settings(BaseSettings):
    app_name: str = "EasyChecker Backend"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./app.db"
    debug: bool = False
    failed_login_threshold: int = 5
    failed_login_window_minutes: int = 5
    suspicious_process_threshold: int = 3
    suspicious_process_window_minutes: int = 5

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug_value(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug"}:
                return True
            if normalized in {"0", "false", "no", "off", "release"}:
                return False
        raise ValueError("DEBUG must be a boolean-like value.")

    @property
    def sqlite_db_path(self) -> Path:
        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix):
            raise ValueError("DATABASE_URL must use sqlite:/// for this project.")

        raw_path = self.database_url[len(prefix) :]
        db_path = Path(raw_path)
        if not db_path.is_absolute():
            db_path = BACKEND_DIR / raw_path
        return db_path.resolve()


@lru_cache
def get_settings() -> Settings:
    # Cache settings so the whole process shares one consistent config object.
    return Settings()
