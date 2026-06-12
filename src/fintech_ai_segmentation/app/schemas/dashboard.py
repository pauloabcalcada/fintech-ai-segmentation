"""Pydantic response models for dashboard endpoints.

``DashboardSummaryResponse``   — top-level wrapper for /dashboard/summary:
    KpiCards                   — total customers, at-risk count, per-cluster
                                 breakdown with avg RFM and avg CAC
    AcquisitionCostByChannel   — average CAC per acquisition channel
    PopulationByProductsOwned  — customer count bucketed by number of products
    ProductOwnershipVsTenure   — avg tenure per products-owned bucket (bubble chart)
    MostCommonProduct          — active ownership count per product type

``DashboardAggregatesResponse`` — top-level wrapper for /dashboard/aggregates:
    CohortActivityEntry        — one cell of the retention heatmap
                                 (cohort_month × activity_month)
    ChannelM6RetentionEntry    — M6 retention rate per channel per cohort
"""

from __future__ import annotations

from pydantic import BaseModel


class ClusterKpi(BaseModel):
    cluster_name: str
    customer_count: int
    pct_of_total: float
    avg_rfm_score: float
    avg_acquisition_cost: float


class KpiCards(BaseModel):
    total_customers: int
    no_transaction_count: int
    at_risk_count: int
    by_cluster: list[ClusterKpi]


class AcquisitionCostByChannel(BaseModel):
    acquisition_channel: str
    avg_acquisition_cost: float


class PopulationByProductsOwned(BaseModel):
    products_owned_count: int
    customer_count: int


class ProductOwnershipVsTenure(BaseModel):
    products_owned_count: int
    avg_tenure_months: float
    customer_count: int


class MostCommonProduct(BaseModel):
    product_type: str
    ownership_count: int


class DashboardSummaryResponse(BaseModel):
    kpi_cards: KpiCards
    acquisition_cost_by_channel: list[AcquisitionCostByChannel]
    population_by_products_owned: list[PopulationByProductsOwned]
    product_ownership_vs_tenure: list[ProductOwnershipVsTenure]
    most_common_products: list[MostCommonProduct]


class CohortActivityEntry(BaseModel):
    cohort_month: str
    activity_month: str
    active_rate: float
    cohort_size: int


class ChannelM6RetentionEntry(BaseModel):
    acquisition_channel: str
    cohort_month: str
    m6_active_rate: float
    cohort_size: int


class DashboardAggregatesResponse(BaseModel):
    cohort_activity_matrix: list[CohortActivityEntry]
    channel_m6_retention: list[ChannelM6RetentionEntry]
