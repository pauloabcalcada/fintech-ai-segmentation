from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from fintech_ai_segmentation.app.repositories.customer import (
    CustomerRepository,
    get_customer_repository,
)
from fintech_ai_segmentation.app.schemas.customer import (
    CustomerListResponse,
    CustomerProfileResponse,
)

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
) -> CustomerProfileResponse:
    profile = await repository.get_customer_profile(customer_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    timeline = await repository.get_activity_timeline(customer_id)
    return CustomerProfileResponse(data=profile, activity_timeline=timeline)
