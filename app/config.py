"""Application configuration via pydantic-settings.

Centralises environment-driven config (database URL, etc.) so the composition
root in ``app.main`` stays disciplined and free of scattered ``os.environ``
look-ups.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings sourced from environment variables / ``.env``."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="CASTNOTE_", extra="ignore")

    # Default targets the docker-compose Postgres defined in the justfile.
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/castnote"
    echo_sql: bool = False
    app_title: str = "NHS Case Notes Tracking API"


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""
    return Settings()
