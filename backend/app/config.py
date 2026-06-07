"""Settings loaded from environment variables.

Stdlib only. No pydantic. Returns a simple namespace object so
existing callers that do `settings.database_url` keep working.
"""

import os
from types import SimpleNamespace


def get_env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def get_cors_origins() -> list[str]:
    raw = get_env("CORS_ORIGINS", "*").strip()
    if not raw:
        return ["*"]
    return [p.strip() for p in raw.split(",") if p.strip()]


_cached = None


def get_settings() -> SimpleNamespace:
    global _cached
    if _cached is not None:
        return _cached
    _cached = SimpleNamespace(
        env=get_env("ENV", "dev"),
        log_level=get_env("LOG_LEVEL", "INFO"),
        database_url=get_env(
            "DATABASE_URL",
            "sqlite+aiosqlite:///./eter-agent.db",
        ),
        ws_shared_secret=get_env("WS_SHARED_SECRET", "CHANGE_ME_IN_PROD"),
        github_oauth_client_id=get_env("GITHUB_OAUTH_CLIENT_ID", ""),
        github_oauth_client_secret=get_env("GITHUB_OAUTH_CLIENT_SECRET", ""),
        railway_master_token=get_env("RAILWAY_MASTER_TOKEN", ""),
        vapid_public_key=get_env("VAPID_PUBLIC_KEY", ""),
        vapid_private_key=get_env("VAPID_PRIVATE_KEY", ""),
        vapid_claims_email=get_env("VAPID_CLAIMS_EMAIL", "mailto:admin@example.com"),
        public_base_url=get_env("PUBLIC_BASE_URL", "http://localhost:8000"),
        cors_origins=get_cors_origins(),
    )
    return _cached
