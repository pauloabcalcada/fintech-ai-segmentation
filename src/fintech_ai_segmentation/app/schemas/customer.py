from __future__ import annotations

import uuid

from pydantic import BaseModel


class CustomerSummary(BaseModel):
    customer_id: uuid.UUID
    name: str
    email: str
    age: int
    state: str
    cluster_name: str | None
    lifecycle_stage: str | None
    rfm_score: float | None
    recency_days: int | None


class CustomerListResponse(BaseModel):
    data: list[CustomerSummary]
    total: int
    page: int
    page_size: int
