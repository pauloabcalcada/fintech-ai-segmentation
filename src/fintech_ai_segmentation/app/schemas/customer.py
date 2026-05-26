from __future__ import annotations

import uuid
from datetime import date

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


class RFMAverages(BaseModel):
    recency_score: float
    frequency_score: float
    monetary_score: float
    rfm_score: float


class ClusterProductProfile(BaseModel):
    wallet_pct: float
    credit_card_pct: float
    investment_pct: float
    insurance_pct: float
    loan_pct: float


class ActivityTimelineEntry(BaseModel):
    year_month: str  # "2024-01"
    tx_count: int
    total_amount: float


class CustomerProfile(BaseModel):
    customer_id: uuid.UUID
    name: str
    email: str
    age: int
    state: str
    acquisition_channel: str
    acquisition_cost: float
    registration_date: date
    tenure_months: int
    cluster_name: str | None
    lifecycle_stage: str | None
    rfm_score: float | None
    recency_score: float | None
    frequency_score: float | None
    monetary_score: float | None
    recency_days: int | None
    products_owned_count: int
    has_wallet: bool
    has_credit_card: bool
    has_investment: bool
    has_insurance: bool
    has_loan: bool
    cluster_position: str | None  # bottom_20 | mid_60 | top_20
    cluster_averages: RFMAverages | None
    population_averages: RFMAverages | None
    cluster_product_profile: ClusterProductProfile | None
    cached_recommendation: dict | None = None
    activity_trend_ratio: float | None = None
    avg_ticket: float | None = None
    avg_days_between_tx: float | None = None
    activity_trend_percentile: float | None = None
    acquisition_cost_percentile: float | None = None
    recency_percentile: float | None = None
    avg_ticket_percentile: float | None = None
    avg_days_between_tx_percentile: float | None = None


class CustomerProfileResponse(BaseModel):
    data: CustomerProfile
    activity_timeline: list[ActivityTimelineEntry]
