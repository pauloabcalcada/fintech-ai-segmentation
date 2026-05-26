from __future__ import annotations

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from fintech_ai_segmentation.app.database import get_engine
from fintech_ai_segmentation.app.schemas.dashboard import (
    AcquisitionCostByChannel,
    ChannelM6RetentionEntry,
    ClusterKpi,
    CohortActivityEntry,
    DashboardAggregatesResponse,
    DashboardSummaryResponse,
    KpiCards,
    MostCommonProduct,
    PopulationByProductsOwned,
    ProductOwnershipVsTenure,
)


class DashboardRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def get_summary(self) -> DashboardSummaryResponse:
        async with self._engine.connect() as conn:
            # KPI: total from customers_raw, no_transaction_count, at_risk
            kpi_row = (await conn.execute(text("""
                SELECT
                    (SELECT COUNT(*)::int FROM customers_raw)           AS total_customers,
                    COUNT(*) FILTER (
                        WHERE cluster_name IS NULL
                    )::int                                              AS no_transaction_count,
                    COUNT(*) FILTER (
                        WHERE lifecycle_stage = 'churned'
                           OR recency_days > 90
                    )::int                                              AS at_risk_count
                FROM customer_analysis
            """))).mappings().one()

            cluster_rows = (await conn.execute(text("""
                SELECT
                    ca.cluster_name,
                    COUNT(*)::int                       AS customer_count,
                    AVG(ca.rfm_score)::float            AS avg_rfm_score,
                    AVG(cr.acquisition_cost)::float     AS avg_acquisition_cost
                FROM customer_analysis ca
                JOIN customers_raw cr ON cr.customer_id::text = ca.customer_id
                WHERE ca.cluster_name IS NOT NULL
                GROUP BY ca.cluster_name
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

            # Product ownership bubble: group by products_owned_count, compute mean tenure and count
            tenure_rows = (await conn.execute(text("""
                SELECT
                    (
                        has_wallet::int + has_credit_card::int + has_investment::int
                        + has_insurance::int + has_loan::int
                    )                          AS products_owned_count,
                    AVG(tenure_months)::float  AS avg_tenure_months,
                    COUNT(*)::int              AS customer_count
                FROM customer_analysis
                GROUP BY products_owned_count
                ORDER BY products_owned_count
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

        total = kpi_row["total_customers"] or 1
        kpi = KpiCards(
            total_customers=kpi_row["total_customers"],
            no_transaction_count=kpi_row["no_transaction_count"],
            at_risk_count=kpi_row["at_risk_count"],
            by_cluster=[
                ClusterKpi(
                    cluster_name=r["cluster_name"],
                    customer_count=r["customer_count"],
                    pct_of_total=round(r["customer_count"] / total * 100, 2),
                    avg_rfm_score=round(r["avg_rfm_score"] or 0.0, 2),
                    avg_acquisition_cost=round(r["avg_acquisition_cost"] or 0.0, 2),
                )
                for r in cluster_rows
            ],
        )

        return DashboardSummaryResponse(
            kpi_cards=kpi,
            acquisition_cost_by_channel=[
                AcquisitionCostByChannel(**dict(r)) for r in acq_rows
            ],
            population_by_products_owned=[
                PopulationByProductsOwned(**dict(r)) for r in pop_rows
            ],
            product_ownership_vs_tenure=[
                ProductOwnershipVsTenure(**dict(r)) for r in tenure_rows
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
            cohort_activity_matrix=[
                CohortActivityEntry(**dict(r)) for r in cohort_rows
            ],
            channel_m6_retention=[
                ChannelM6RetentionEntry(**dict(r)) for r in retention_rows
            ],
        )


def get_dashboard_repository(
    engine: AsyncEngine = Depends(get_engine),
) -> DashboardRepository:
    return DashboardRepository(engine)
