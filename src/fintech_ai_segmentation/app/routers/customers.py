"""Customer endpoints.

Four routes:

GET  /customers            — paginated, filterable list (cluster, lifecycle,
                             channel, free-text search). Max page_size = 100.
GET  /customers/sample     — random sample of N customers per cluster; used by
                             the frontend landing view before a filter is applied.
GET  /customers/{id}       — full profile with RFM scores, cluster context,
                             product ownership, and the most recent cached
                             recommendation (if any, within 24h).
POST /customers/{id}/analyze — triggers the LangGraph agent. Checks the rate
                             limiter first (returns cached result or 429 if
                             blocked), then acquires a semaphore slot to cap
                             concurrent LLM calls at 2. Returns 503 if both
                             slots are busy rather than queueing indefinitely.
"""

from __future__ import annotations

import asyncio
import uuid

from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from fintech_ai_segmentation.app.client_ip import get_client_ip
from fintech_ai_segmentation.app.repositories.customer import (
    CustomerRepository,
    get_customer_repository,
)
from fintech_ai_segmentation.app.repositories.recommendation import (
    Blocked,
    CachedResult,
    RateLimiter,
    RecommendationLogStore,
    get_rate_limiter,
    get_recommendation_agent,
    get_recommendation_log_store,
)
from fintech_ai_segmentation.app.schemas.customer import (
    CustomerListResponse,
    CustomerProfileResponse,
)
from fintech_ai_segmentation.app.settings import Settings, get_settings

_MODEL = "smart-auto"

# How long to wait for a free analysis slot before rejecting with 503. A free
# slot is acquired immediately; this only bounds the wait when both slots are
# busy, so the LLM is never overloaded.
_ANALYZE_ACQUIRE_TIMEOUT = 0.05


class AnalyzeRequest(BaseModel):
    language: Literal["en", "pt-BR"] = "en"


router = APIRouter()

_analyze_semaphore = asyncio.Semaphore(10)


@router.get("/customers", response_model=CustomerListResponse)
async def list_customers(
    cluster: str | None = None,
    lifecycle_stage: str | None = None,
    channel: str | None = None,
    q: str | None = None,
    sort: str = "rfm_score",
    order: str = "desc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    repository: CustomerRepository = Depends(get_customer_repository),
) -> CustomerListResponse:
    customers, total = await repository.list_customers(
        cluster=cluster,
        lifecycle_stage=lifecycle_stage,
        channel=channel,
        q=q,
        sort=sort,
        order=order,
        page=page,
        page_size=page_size,
    )
    return CustomerListResponse(
        data=customers, total=total, page=page, page_size=page_size
    )


@router.get("/customers/sample", response_model=CustomerListResponse)
async def sample_customers(
    per_cluster: int = Query(default=2, ge=1, le=5),
    repository: CustomerRepository = Depends(get_customer_repository),
) -> CustomerListResponse:
    customers = await repository.sample_customers(per_cluster)
    return CustomerListResponse(
        data=customers, total=len(customers), page=1, page_size=per_cluster * 3
    )


@router.get("/customers/{customer_id}", response_model=CustomerProfileResponse)
async def get_customer(
    customer_id: uuid.UUID,
    language: str = Query(default="en"),
    repository: CustomerRepository = Depends(get_customer_repository),
    log_store: RecommendationLogStore = Depends(get_recommendation_log_store),
) -> CustomerProfileResponse:
    profile = await repository.get_customer_profile(customer_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    timeline = await repository.get_activity_timeline(customer_id)
    profile.cached_recommendation = await log_store.get_cached_recommendation(
        customer_id, language
    )
    return CustomerProfileResponse(data=profile, activity_timeline=timeline)


@router.post("/customers/{customer_id}/analyze")
async def analyze_customer(
    customer_id: uuid.UUID,
    body: AnalyzeRequest,
    request: Request,
    repository: CustomerRepository = Depends(get_customer_repository),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
    log_store: RecommendationLogStore = Depends(get_recommendation_log_store),
    agent: Any = Depends(get_recommendation_agent),
    settings: Settings = Depends(get_settings),
) -> dict:
    profile = await repository.get_customer_profile(customer_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    ip = get_client_ip(request, settings.TRUSTED_PROXY_HOPS)
    result = await rate_limiter.check(customer_id, ip, language=body.language)

    if isinstance(result, CachedResult):
        return {
            "cached": True,
            "generated_at": result.generated_at.isoformat(),
            "model_used": result.model_used,
            "recommendation": result.recommendation_json,
        }

    if isinstance(result, Blocked):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "retry_after": result.retry_after.isoformat(),
            },
        )

    # Acquire a slot atomically: a free slot is taken without waiting; if both
    # are busy we reject with 503 rather than queueing indefinitely. Using
    # wait_for avoids the check-then-acquire race of inspecting the semaphore.
    try:
        await asyncio.wait_for(
            _analyze_semaphore.acquire(), timeout=_ANALYZE_ACQUIRE_TIMEOUT
        )
    except (asyncio.TimeoutError, TimeoutError):
        raise HTTPException(
            status_code=503,
            detail={
                "error": "server_busy",
                "message": "Too many analysis requests in progress. Please try again in a moment.",
            },
        )

    try:
        recommendation = await agent.run(customer_id, _MODEL, language=body.language)
    except Exception as exc:
        import openai

        if isinstance(exc, openai.RateLimitError):
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "provider_rate_limited",
                    "message": "The AI provider is temporarily unavailable for this model. Try a different model.",
                },
            )
        raise
    finally:
        _analyze_semaphore.release()

    rec_json = recommendation.model_dump()
    await log_store.record(customer_id, ip, _MODEL, rec_json, language=body.language)
    return {
        "cached": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_used": _MODEL,
        "recommendation": rec_json,
    }
