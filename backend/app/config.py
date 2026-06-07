"""Centralized settings loaded from environment variables.

Single source of truth for connection strings, secrets, and feature flags.
All values come from the environment (or a local .env in dev); no defaults
that would silently work in production.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Runtime
    env: Literal["dev", "staging", "prod"] = "dev"
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    # Database
    database_url: str = "sqlite+aiosqlite:///./eter-agent.db"
    # Examples:
    #   sqlite+aiosqlite:///./eter-agent.db
    #   postgresql+asyncpg://user:pass@host:5432/eter_agent

    # WebSocket auth
    ws_shared_secret: str = "CHANGE_ME_IN_PROD"

    # GitHub OAuth (for PWA login)
    github_oauth_client_id: str = ""
    github_oauth_client_secret: str = ""

    # Railway personal token (only used if PWA pushes tokens down to Mac)
    # Railway does not support 3rd-party OAuth; we accept a manually-pasted token.
    railway_master_token: str = ""

    # Web Push (VAPID) for "approval needed" phone notifications
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_claims_email: str = "mailto:admin@example.com"

    # Cross-origin / domain
    public_base_url: str = "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
