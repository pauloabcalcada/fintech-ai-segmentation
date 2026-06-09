from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from fintech_ai_segmentation.app.database import get_engine
from fintech_ai_segmentation.app.settings import get_settings


def _parse_dt(value) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _parse_json(value) -> dict:
    if isinstance(value, dict):
        return value
    return json.loads(value)


@dataclass
class Allowed:
    pass


@dataclass
class CachedResult:
    recommendation_json: dict
    generated_at: datetime
    model_used: str


@dataclass
class Blocked:
    retry_after: datetime


RateLimitResult = Allowed | CachedResult | Blocked


class RecommendationLogStore:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def get_cached_recommendation(
        self, customer_id: uuid.UUID, language: str = "en"
    ) -> dict | None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        async with self._engine.connect() as conn:
            row = await conn.execute(
                text(
                    "SELECT recommendation_json, generated_at, model_used "
                    "FROM recommendation_log "
                    "WHERE customer_id = :customer_id AND language = :language AND generated_at >= :cutoff "
                    "ORDER BY generated_at DESC LIMIT 1"
                ),
                {
                    "customer_id": str(customer_id),
                    "language": language,
                    "cutoff": cutoff,
                },
            )
            cached = row.mappings().first()
            if not cached:
                return None
            return {
                "generated_at": _parse_dt(cached["generated_at"]).isoformat(),
                "model_used": cached["model_used"],
                "recommendation": _parse_json(cached["recommendation_json"]),
            }

    async def record(
        self,
        customer_id: uuid.UUID,
        ip_address: str,
        model_used: str,
        recommendation_json: dict,
        language: str = "en",
    ) -> None:
        async with self._engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO recommendation_log "
                    "(customer_id, ip_address, model_used, language, recommendation_json) "
                    "VALUES (:customer_id, :ip_address, :model_used, :language, CAST(:recommendation_json AS jsonb))"
                ),
                {
                    "customer_id": str(customer_id),
                    "ip_address": ip_address,
                    "model_used": model_used,
                    "language": language,
                    "recommendation_json": __import__("json").dumps(
                        recommendation_json
                    ),
                },
            )


class RateLimiter:
    def __init__(self, engine: AsyncEngine, max_per_ip_daily: int) -> None:
        self._engine = engine
        self._max = max_per_ip_daily

    async def check(
        self, customer_id: uuid.UUID, ip_address: str, language: str = "en"
    ) -> RateLimitResult:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        async with self._engine.connect() as conn:
            row = await conn.execute(
                text(
                    "SELECT recommendation_json, generated_at, model_used "
                    "FROM recommendation_log "
                    "WHERE customer_id = :customer_id AND language = :language AND generated_at >= :cutoff "
                    "ORDER BY generated_at DESC LIMIT 1"
                ),
                {
                    "customer_id": str(customer_id),
                    "language": language,
                    "cutoff": cutoff,
                },
            )
            cached = row.mappings().first()
            if cached:
                return CachedResult(
                    recommendation_json=_parse_json(cached["recommendation_json"]),
                    generated_at=_parse_dt(cached["generated_at"]),
                    model_used=cached["model_used"],
                )

            ip_rows = await conn.execute(
                text(
                    "SELECT generated_at FROM recommendation_log "
                    "WHERE ip_address = :ip AND generated_at >= :cutoff "
                    "ORDER BY generated_at ASC"
                ),
                {"ip": ip_address, "cutoff": cutoff},
            )
            ip_entries = ip_rows.mappings().all()
            if len(ip_entries) >= self._max:
                oldest = _parse_dt(ip_entries[0]["generated_at"])
                return Blocked(retry_after=oldest + timedelta(hours=24))

        return Allowed()


def get_recommendation_log_store() -> RecommendationLogStore:
    return RecommendationLogStore(get_engine())


def get_rate_limiter() -> RateLimiter:
    settings = get_settings()
    return RateLimiter(get_engine(), settings.MAX_PER_IP_DAILY)


def get_recommendation_agent():
    from fintech_ai_segmentation.agent.llm_client import OpenRouterLLMClient
    from fintech_ai_segmentation.agent.recommendation_agent import (
        LangGraphRecommendationAgent,
    )
    from fintech_ai_segmentation.app.repositories.customer import CustomerRepository

    settings = get_settings()
    llm_client = OpenRouterLLMClient(settings.OPENROUTER_API_KEY)
    engine = get_engine()
    repository = CustomerRepository(engine)
    return LangGraphRecommendationAgent(llm_client, repository)
