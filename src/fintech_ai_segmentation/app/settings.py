from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SUPABASE_DATABASE_URL: str = ""
    OPENROUTER_API_KEY: str = ""
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = ""
    MAX_PER_IP_DAILY: int = 10
    # Number of trusted reverse proxies in front of the app. Used to pick the
    # real client IP from the X-Forwarded-For chain. Railway = 1 hop.
    TRUSTED_PROXY_HOPS: int = 1
    # Secure by default: docs (/docs, /redoc) are only exposed when this is
    # explicitly set to "development". A missing value in production stays safe.
    ENVIRONMENT: str = "production"
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    VERSION: str = "0.1.0"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
