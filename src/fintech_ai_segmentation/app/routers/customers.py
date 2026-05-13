from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from fintech_ai_segmentation.app.repositories.customer import (
    CustomerRepository,
    get_customer_repository,
)
from fintech_ai_segmentation.app.schemas.customer import CustomerListResponse

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
