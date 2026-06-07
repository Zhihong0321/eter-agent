"""Centralized settings loaded from environment variables.

Single source of truth for connection strings, secrets, and feature flags.
All values come from the environment; no .env lookup in production.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=None,  # no .env in production; Railway injects env vars
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

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, v):
        """Accept JSON arrays, comma-separated strings, or single values."""
        if v is None or v == "":
            return ["*"]
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("["):
                # JSON array
                import json
                return json.loads(s)
            # Comma-separated or single value
            return [p.strip() for p in s.split(",") if p.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
