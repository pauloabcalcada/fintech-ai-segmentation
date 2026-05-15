from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from fintech_ai_segmentation.app.repositories.recommendation import (
    Allowed,
    Blocked,
    CachedResult,
    RateLimiter,
    RecommendationLogStore,
)

# ---------------------------------------------------------------------------
# Async SQLite fixture — creates the recommendation_log table in-process
# ---------------------------------------------------------------------------

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS recommendation_log (
    id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    customer_id     TEXT NOT NULL,
    ip_address      TEXT NOT NULL,
    model_used      TEXT NOT NULL,
    generated_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    recommendation_json TEXT NOT NULL
)
"""

_CUSTOMER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_OTHER_CUSTOMER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
_IP = "192.168.1.1"
_OTHER_IP = "10.0.0.1"
_MAX_DAILY = 3

_SAMPLE_REC = json.dumps({"risk_level": "critical", "recommended_action": "test"})


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with eng.begin() as conn:
        await conn.execute(text(_CREATE_TABLE))
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def limiter(engine):
    return RateLimiter(engine, _MAX_DAILY)


@pytest_asyncio.fixture
async def log_store(engine):
    return RecommendationLogStore(engine)


async def _insert_log(engine, customer_id, ip, model, generated_at: datetime):
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO recommendation_log "
                "(customer_id, ip_address, model_used, generated_at, recommendation_json) "
                "VALUES (:cid, :ip, :model, :ts, :rec)"
            ),
            {
                "cid": str(customer_id),
                "ip": ip,
                "model": model,
                "ts": generated_at,
                "rec": _SAMPLE_REC,
            },
        )


# ---------------------------------------------------------------------------
# Cycle 9 — Allowed when no log entries
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rate_limiter_allowed_when_no_entries(limiter) -> None:
    result = await limiter.check(_CUSTOMER_ID, _IP)
    assert isinstance(result, Allowed)


# ---------------------------------------------------------------------------
# Cycle 10 — CachedResult when customer has a recent log entry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rate_limiter_cached_result_for_recent_customer_entry(limiter, engine) -> None:
    recent = datetime.now(timezone.utc) - timedelta(hours=1)
    await _insert_log(engine, _CUSTOMER_ID, _IP, "gemini-flash-free", recent)

    result = await limiter.check(_CUSTOMER_ID, _IP)
    assert isinstance(result, CachedResult)
    assert result.model_used == "gemini-flash-free"


# ---------------------------------------------------------------------------
# Cycle 11 — Blocked with correct retry_after when IP limit hit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rate_limiter_blocked_when_ip_limit_exceeded(limiter, engine) -> None:
    base = datetime.now(timezone.utc) - timedelta(hours=2)
    for i in range(_MAX_DAILY):
        await _insert_log(engine, _OTHER_CUSTOMER_ID, _IP, "smart-auto", base + timedelta(minutes=i))

    result = await limiter.check(_CUSTOMER_ID, _IP)
    assert isinstance(result, Blocked)
    expected_retry = base + timedelta(hours=24)
    assert abs((result.retry_after - expected_retry).total_seconds()) < 2


# ---------------------------------------------------------------------------
# Cycle 12 — entries older than 24h are ignored
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rate_limiter_ignores_entries_older_than_24h(limiter, engine) -> None:
    old = datetime.now(timezone.utc) - timedelta(hours=25)
    for i in range(_MAX_DAILY):
        await _insert_log(engine, _OTHER_CUSTOMER_ID, _IP, "smart-auto", old + timedelta(minutes=i))

    result = await limiter.check(_CUSTOMER_ID, _IP)
    assert isinstance(result, Allowed)
