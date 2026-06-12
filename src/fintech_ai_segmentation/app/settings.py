"""Application settings loaded from environment variables and .env file.

Pydantic-settings reads values from the environment first, then falls back
to ``.env``. The ``@lru_cache`` on ``get_settings()`` means the file is
parsed exactly once per process — callers can import and call ``get_settings()``
freely without re-reading disk.

Defaults are chosen to be safe when a variable is missing in production:
- ``ENVIRONMENT`` defaults to ``"production"``, so docs are hidden unless
  explicitly overridden to ``"development"``.
- ``TRUSTED_PROXY_HOPS`` defaults to 1 (Railway's single proxy layer).
- ``IP_HASH_SALT`` defaults to ``""`` — workable but weaker; set a real value
  in Railway Variables to prevent brute-forcing rate-limit records.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SUPABASE_DATABASE_URL: str = ""
    OPENROUTER_API_KEY: str = ""
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = ""
    MAX_PER_IP_DAILY: int = 10
    # Secret salt for hashing client IPs before they are stored. IPv4 space is
    # small enough to brute-force an unsalted hash, so set a stable random
    # value in production. Must not change, or existing rate-limit counts reset.
    IP_HASH_SALT: str = ""
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
