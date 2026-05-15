from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from fintech_ai_segmentation.app.middleware import require_demo_password
from fintech_ai_segmentation.app.repositories.customer import (
    CustomerRepository,
    get_customer_repository,
)
from fintech_ai_segmentation.app.repositories.recommendation import (
    Allowed,
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


class AnalyzeRequest(BaseModel):
    model: Literal["gemini-flash-free", "llama-70b-free", "mistral-7b-free", "smart-auto"]


router = APIRouter()


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
    return CustomerListResponse(data=customers, total=total, page=page, page_size=page_size)


@router.get("/customers/{customer_id}", response_model=CustomerProfileResponse)
async def get_customer(
    customer_id: uuid.UUID,
    repository: CustomerRepository = Depends(get_customer_repository),
    log_store: RecommendationLogStore = Depends(get_recommendation_log_store),
) -> CustomerProfileResponse:
    profile = await repository.get_customer_profile(customer_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    timeline = await repository.get_activity_timeline(customer_id)
    profile.cached_recommendation = await log_store.get_cached_recommendation(customer_id)
    return CustomerProfileResponse(data=profile, activity_timeline=timeline)


@router.post("/customers/{customer_id}/analyze")
async def analyze_customer(
    customer_id: uuid.UUID,
    body: AnalyzeRequest,
    request: Request,
    _: None = Depends(require_demo_password),
    repository: CustomerRepository = Depends(get_customer_repository),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
    log_store: RecommendationLogStore = Depends(get_recommendation_log_store),
    agent: Any = Depends(get_recommendation_agent),
) -> dict:
    profile = await repository.get_customer_profile(customer_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    ip = request.client.host if request.client else "unknown"
    result = await rate_limiter.check(customer_id, ip)

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

    try:
        recommendation = await agent.run(customer_id, body.model)
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

    rec_json = recommendation.model_dump()
    await log_store.record(customer_id, ip, body.model, rec_json)
    return {
        "cached": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_used": body.model,
        "recommendation": rec_json,
    }
