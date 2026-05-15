from __future__ import annotations

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from fintech_ai_segmentation.app.database import get_engine
from fintech_ai_segmentation.app.schemas.dashboard import (
    AcquisitionCostByChannel,
    ChannelM6RetentionEntry,
    CohortActivityEntry,
    DashboardAggregatesResponse,
    DashboardSummaryResponse,
    KpiCards,
    MostCommonProduct,
    PopulationByProductsOwned,
    ProductOwnershipVsTenure,
    SegmentBreakdown,
)

_TENURE_CASE = """
    CASE
        WHEN tenure_months < 6   THEN '0-6m'
        WHEN tenure_months < 12  THEN '6-12m'
        WHEN tenure_months < 24  THEN '12-24m'
        ELSE '24m+'
    END
"""

_TENURE_ORDER = {"0-6m": 0, "6-12m": 1, "12-24m": 2, "24m+": 3}


class DashboardRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def get_summary(self) -> DashboardSummaryResponse:
        async with self._engine.connect() as conn:
            # KPI: total + by_cluster + avg_rfm + at_risk
            kpi_row = (await conn.execute(text("""
                SELECT
                    COUNT(*)::int                                        AS total_customers,
                    AVG(rfm_score)::float                               AS avg_rfm_score,
                    COUNT(*) FILTER (
                        WHERE lifecycle_stage = 'churned'
                           OR recency_days > 90
                    )::int                                              AS at_risk_count
                FROM customer_analysis
            """))).mappings().one()

            cluster_rows = (await conn.execute(text("""
                SELECT cluster_name, COUNT(*)::int AS customer_count
                FROM customer_analysis
                WHERE cluster_name IS NOT NULL
                GROUP BY cluster_name
                ORDER BY customer_count DESC
            """))).mappings().all()

            # Acquisition cost by channel
            acq_rows = (await conn.execute(text("""
                SELECT
                    acquisition_channel,
                    AVG(acquisition_cost)::float AS avg_acquisition_cost
                FROM customers_raw
                GROUP BY acquisition_channel
                ORDER BY acquisition_channel
            """))).mappings().all()

            # Population by products owned (0-5)
            pop_rows = (await conn.execute(text("""
                SELECT
                    (
                        has_wallet::int + has_credit_card::int + has_investment::int
                        + has_insurance::int + has_loan::int
                    ) AS products_owned_count,
                    COUNT(*)::int AS customer_count
                FROM customer_analysis
                GROUP BY products_owned_count
                ORDER BY products_owned_count
            """))).mappings().all()

            # Product ownership vs tenure bucket
            tenure_rows = (await conn.execute(text(f"""
                SELECT
                    {_TENURE_CASE} AS tenure_bucket,
                    AVG(
                        has_wallet::int + has_credit_card::int + has_investment::int
                        + has_insurance::int + has_loan::int
                    )::float AS avg_products_owned
                FROM customer_analysis
                GROUP BY tenure_bucket
                ORDER BY MIN(tenure_months)
            """))).mappings().all()

            # Most common products (active ownership count per product type)
            product_rows = (await conn.execute(text("""
                SELECT
                    pr.product_type,
                    COUNT(*)::int AS ownership_count
                FROM customer_products_raw cpr
                JOIN products_raw pr ON pr.product_id = cpr.product_id
                WHERE cpr.is_active = TRUE
                GROUP BY pr.product_type
                ORDER BY ownership_count DESC
            """))).mappings().all()

        kpi = KpiCards(
            total_customers=kpi_row["total_customers"],
            by_cluster=[SegmentBreakdown(**dict(r)) for r in cluster_rows],
            avg_rfm_score=round(kpi_row["avg_rfm_score"] or 0.0, 2),
            at_risk_count=kpi_row["at_risk_count"],
        )

        return DashboardSummaryResponse(
            kpi_cards=kpi,
            acquisition_cost_by_channel=[AcquisitionCostByChannel(**dict(r)) for r in acq_rows],
            population_by_products_owned=[PopulationByProductsOwned(**dict(r)) for r in pop_rows],
            product_ownership_vs_tenure=[
                ProductOwnershipVsTenure(**dict(r))
                for r in sorted(tenure_rows, key=lambda r: _TENURE_ORDER.get(r["tenure_bucket"], 99))
            ],
            most_common_products=[MostCommonProduct(**dict(r)) for r in product_rows],
        )

    async def get_aggregates(self) -> DashboardAggregatesResponse:
        async with self._engine.connect() as conn:
            cohort_rows = (await conn.execute(text("""
                SELECT
                    TO_CHAR(cohort_month, 'YYYY-MM')   AS cohort_month,
                    TO_CHAR(activity_month, 'YYYY-MM') AS activity_month,
                    active_rate::float,
                    cohort_size::int
                FROM cohort_activity_matrix
                ORDER BY cohort_month, activity_month
            """))).mappings().all()

            retention_rows = (await conn.execute(text("""
                SELECT
                    acquisition_channel,
                    TO_CHAR(cohort_month, 'YYYY-MM') AS cohort_month,
                    m6_active_rate::float,
                    cohort_size::int
                FROM channel_m6_retention
                ORDER BY cohort_month, acquisition_channel
            """))).mappings().all()

        return DashboardAggregatesResponse(
            cohort_activity_matrix=[CohortActivityEntry(**dict(r)) for r in cohort_rows],
            channel_m6_retention=[ChannelM6RetentionEntry(**dict(r)) for r in retention_rows],
        )


def get_dashboard_repository(engine: AsyncEngine = Depends(get_engine)) -> DashboardRepository:
    return DashboardRepository(engine)
