from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    scenario_id: str = "smart_ev_cockpit"
    powercontext_backend: Literal["builtin"] = "builtin"
    powercontext_scope_id: str = "smart-ev-cockpit"
    powercontext_database_url: str = (
        "sqlite+aiosqlite:///data/powercontext_smart_ev.db"
    )
    powercontext_operation_timeout_seconds: float = Field(default=30.0, gt=0)
    demo_privacy_mode: str = "strict"
    llm_provider: str = "openai"
    llm_model: str | None = None
    llm_api_key: str | None = None
    openai_llm_base_url: str | None = None
    chat_history_db_path: str = "data/chat_history.sqlite3"
    identity_db_path: str = "data/user_identities.sqlite3"

    model_config = SettingsConfigDict(
        env_file=(
            REPOSITORY_ROOT / ".env",
            BACKEND_ROOT / ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )


def get_settings() -> Settings:
    return Settings()
