"""Async SQLAlchemy engine lifecycle management.

A single global ``AsyncEngine`` is created at startup via ``init_db()`` and
disposed at shutdown via ``close_db()``. All repositories receive the engine
via ``get_engine()``, which raises if called before ``init_db()`` completes.

``pool_pre_ping=True`` sends a lightweight ``SELECT 1`` before each connection
is handed to a query, so stale connections from Supabase's idle-timeout are
detected and recycled transparently rather than causing mid-request errors.

The URL rewrite from ``postgresql://`` to ``postgresql+asyncpg://`` is needed
because SQLAlchemy's async interface requires an async driver; asyncpg is the
standard choice for PostgreSQL.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from fintech_ai_segmentation.app.settings import get_settings

_engine: AsyncEngine | None = None


async def init_db() -> None:
    global _engine
    settings = get_settings()
    url = settings.SUPABASE_DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    _engine = create_async_engine(url, pool_pre_ping=True)
    async with _engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def close_db() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("Database engine not initialized — call init_db() first")
    return _engine
