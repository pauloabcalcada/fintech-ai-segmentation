"""Customer data access layer.

``CustomerRepository`` is the only place in the codebase that reads from
``customer_analysis`` and ``customers_raw``. All SQL is written as SQLAlchemy
``text()`` with named bind parameters — no string interpolation, no injection
risk.

``AggregateCache`` is loaded once at startup (see ``main.py`` lifespan) and
injected into the repository via ``get_customer_repository()``. It holds
cluster-level and population-level RFM averages that are appended to every
``CustomerProfile`` without an extra per-request query.

Key design decisions:
- Sort column is validated against ``_SORT_ALLOWLIST`` before interpolation
  into the ORDER BY clause — the only dynamic SQL in the file.
- ``_PROFILE_SQL`` computes ``cluster_position`` (bottom_20/mid_60/top_20)
  and five population-relative percentiles in a single window-function query
  so the frontend can display contextual rankings without a second round-trip.
- ``get_activity_timeline`` queries ``transactions_raw`` directly (not the mart)
  to show the full raw monthly transaction history sent to the AI agent.
"""

from __future__ import annotations

import uuid

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from fintech_ai_segmentation.app.database import get_engine
from fintech_ai_segmentation.app.schemas.customer import (
    ActivityTimelineEntry,
    ClusterProductProfile,
    CustomerProfile,
    CustomerSummary,
    RFMAverages,
)

_SORT_ALLOWLIST = {"rfm_score", "recency_days", "monetary_total"}
_SEARCH_MAX_LEN = 100

_BASE_FROM = """
    FROM customer_analysis ca
    JOIN customers_raw cr ON cr.customer_id = ca.customer_id::uuid
"""

_PROFILE_SQL = text("""
    WITH full_pop AS (
        SELECT
            cr.customer_id,
            cr.name,
            cr.email,
            cr.age,
            cr.state,
            cr.acquisition_channel,
            cr.acquisition_cost,
            cr.registration_date,
            ca.tenure_months,
            ca.cluster_name,
            ca.lifecycle_stage,
            ca.rfm_score,
            ca.recency_score,
            ca.frequency_score,
            ca.monetary_score,
            ca.recency_days,
            ca.has_wallet,
            ca.has_credit_card,
            ca.has_investment,
            ca.has_insurance,
            ca.has_loan,
            ca.activity_trend_ratio,
            ca.avg_ticket,
            ca.avg_days_between_tx,
            (
                ca.has_wallet::int + ca.has_credit_card::int + ca.has_investment::int
                + ca.has_insurance::int + ca.has_loan::int
            ) AS products_owned_count,
            CASE
                WHEN PERCENT_RANK() OVER (
                    PARTITION BY ca.cluster_name ORDER BY ca.rfm_score
                ) <= 0.20 THEN 'bottom_20'
                WHEN PERCENT_RANK() OVER (
                    PARTITION BY ca.cluster_name ORDER BY ca.rfm_score
                ) >= 0.80 THEN 'top_20'
                ELSE 'mid_60'
            END AS cluster_position,
            PERCENT_RANK() OVER (
                ORDER BY ca.activity_trend_ratio ASC NULLS FIRST
            ) AS activity_trend_percentile,
            1.0 - PERCENT_RANK() OVER (
                ORDER BY ca.acquisition_cost ASC NULLS LAST
            ) AS acquisition_cost_percentile,
            1.0 - PERCENT_RANK() OVER (
                ORDER BY ca.recency_days ASC NULLS LAST
            ) AS recency_percentile,
            PERCENT_RANK() OVER (
                ORDER BY ca.avg_ticket ASC NULLS FIRST
            ) AS avg_ticket_percentile,
            1.0 - PERCENT_RANK() OVER (
                ORDER BY ca.avg_days_between_tx ASC NULLS LAST
            ) AS avg_days_between_tx_percentile
        FROM customer_analysis ca
        JOIN customers_raw cr ON cr.customer_id = ca.customer_id::uuid
    )
    SELECT * FROM full_pop WHERE customer_id = :customer_id
""")


def _build_search_pattern(q: str | None) -> str | None:
    if not q:
        return None
    return f"%{q[:_SEARCH_MAX_LEN]}%"


def _build_where(
    cluster: str | None,
    lifecycle_stage: str | None,
    channel: str | None,
    search: str | None,
) -> tuple[str, dict]:
    conditions: list[str] = []
    params: dict = {}

    if cluster is not None:
        conditions.append("ca.cluster_name = :cluster")
        params["cluster"] = cluster
    if lifecycle_stage is not None:
        conditions.append("ca.lifecycle_stage = :lifecycle")
        params["lifecycle"] = lifecycle_stage
    if channel is not None:
        conditions.append("cr.acquisition_channel = :channel")
        params["channel"] = channel
    if search is not None:
        conditions.append("(cr.name ILIKE :search OR cr.email ILIKE :search)")
        params["search"] = search

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    return where, params


class AggregateCache:
    """Cluster and population aggregates computed once at startup."""

    def __init__(
        self,
        cluster_averages: dict[str, RFMAverages],
        population_averages: RFMAverages,
        cluster_product_profiles: dict[str, ClusterProductProfile],
    ) -> None:
        self.cluster_averages = cluster_averages
        self.population_averages = population_averages
        self.cluster_product_profiles = cluster_product_profiles

    @classmethod
    async def load(cls, engine: AsyncEngine) -> "AggregateCache | None":
        cluster_sql = text("""
            SELECT
                cluster_name,
                AVG(recency_score)  AS recency_score,
                AVG(frequency_score) AS frequency_score,
                AVG(monetary_score) AS monetary_score,
                AVG(rfm_score)      AS rfm_score
            FROM customer_analysis
            GROUP BY cluster_name
        """)
        population_sql = text("""
            SELECT
                AVG(recency_score)  AS recency_score,
                AVG(frequency_score) AS frequency_score,
                AVG(monetary_score) AS monetary_score,
                AVG(rfm_score)      AS rfm_score
            FROM customer_analysis
        """)
        product_sql = text("""
            SELECT
                cluster_name,
                AVG(has_wallet::int)      AS wallet_pct,
                AVG(has_credit_card::int) AS credit_card_pct,
                AVG(has_investment::int)  AS investment_pct,
                AVG(has_insurance::int)   AS insurance_pct,
                AVG(has_loan::int)        AS loan_pct
            FROM customer_analysis
            GROUP BY cluster_name
        """)

        async with engine.connect() as conn:
            cluster_rows = (await conn.execute(cluster_sql)).mappings().all()
            pop_row = (await conn.execute(population_sql)).mappings().one()
            product_rows = (await conn.execute(product_sql)).mappings().all()

        if pop_row["rfm_score"] is None:
            return None

        cluster_averages = {
            row["cluster_name"]: RFMAverages(
                **{
                    k: float(row[k])
                    for k in (
                        "recency_score",
                        "frequency_score",
                        "monetary_score",
                        "rfm_score",
                    )
                }
            )
            for row in cluster_rows
            if row["cluster_name"]
        }
        population_averages = RFMAverages(
            **{
                k: float(pop_row[k])
                for k in (
                    "recency_score",
                    "frequency_score",
                    "monetary_score",
                    "rfm_score",
                )
            }
        )
        cluster_product_profiles = {
            row["cluster_name"]: ClusterProductProfile(
                **{
                    k: float(row[k])
                    for k in (
                        "wallet_pct",
                        "credit_card_pct",
                        "investment_pct",
                        "insurance_pct",
                        "loan_pct",
                    )
                }
            )
            for row in product_rows
            if row["cluster_name"]
        }

        return cls(cluster_averages, population_averages, cluster_product_profiles)


class CustomerRepository:
    def __init__(
        self, engine: AsyncEngine, cache: AggregateCache | None = None
    ) -> None:
        self._engine = engine
        self._cache = cache

    async def list_customers(
        self,
        *,
        cluster: str | None = None,
        lifecycle_stage: str | None = None,
        channel: str | None = None,
        q: str | None = None,
        sort: str = "rfm_score",
        order: str = "desc",
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[CustomerSummary], int]:
        sort_col = sort if sort in _SORT_ALLOWLIST else "rfm_score"
        order_dir = "ASC" if order.lower() == "asc" else "DESC"
        offset = (page - 1) * page_size
        search = _build_search_pattern(q)

        where, filter_params = _build_where(cluster, lifecycle_stage, channel, search)

        count_sql = text(f"SELECT COUNT(*) {_BASE_FROM} {where}")

        rows_sql = text(f"""
            SELECT
                cr.customer_id,
                cr.name,
                cr.email,
                cr.age,
                cr.state,
                ca.cluster_name,
                ca.lifecycle_stage,
                ca.rfm_score,
                ca.recency_days
            {_BASE_FROM}
            {where}
            ORDER BY ca.{sort_col} {order_dir}, ca.customer_id ASC
            LIMIT :limit OFFSET :offset
        """)

        page_params = {**filter_params, "limit": page_size, "offset": offset}

        async with self._engine.connect() as conn:
            total: int = (await conn.execute(count_sql, filter_params)).scalar_one()
            result = await conn.execute(rows_sql, page_params)
            customers = [CustomerSummary(**dict(row._mapping)) for row in result]

        return customers, total

    async def get_customer_profile(
        self, customer_id: uuid.UUID
    ) -> CustomerProfile | None:
        async with self._engine.connect() as conn:
            result = await conn.execute(_PROFILE_SQL, {"customer_id": str(customer_id)})
            row = result.mappings().one_or_none()

        if row is None:
            return None

        cluster = row["cluster_name"]
        cache = self._cache
        cluster_averages = (
            cache.cluster_averages.get(cluster) if cache and cluster else None
        )
        population_averages = cache.population_averages if cache else None
        cluster_product_profile = (
            cache.cluster_product_profiles.get(cluster) if cache and cluster else None
        )

        return CustomerProfile(
            customer_id=row["customer_id"],
            name=row["name"],
            email=row["email"],
            age=row["age"],
            state=row["state"],
            acquisition_channel=row["acquisition_channel"],
            acquisition_cost=float(row["acquisition_cost"]),
            registration_date=row["registration_date"],
            tenure_months=int(row["tenure_months"]),
            cluster_name=cluster,
            lifecycle_stage=row["lifecycle_stage"],
            rfm_score=float(row["rfm_score"]) if row["rfm_score"] is not None else None,
            recency_score=(
                float(row["recency_score"])
                if row["recency_score"] is not None
                else None
            ),
            frequency_score=(
                float(row["frequency_score"])
                if row["frequency_score"] is not None
                else None
            ),
            monetary_score=(
                float(row["monetary_score"])
                if row["monetary_score"] is not None
                else None
            ),
            recency_days=row["recency_days"],
            products_owned_count=row["products_owned_count"],
            has_wallet=row["has_wallet"],
            has_credit_card=row["has_credit_card"],
            has_investment=row["has_investment"],
            has_insurance=row["has_insurance"],
            has_loan=row["has_loan"],
            cluster_position=row["cluster_position"],
            cluster_averages=cluster_averages,
            population_averages=population_averages,
            cluster_product_profile=cluster_product_profile,
            activity_trend_ratio=(
                float(row["activity_trend_ratio"])
                if row["activity_trend_ratio"] is not None
                else None
            ),
            avg_ticket=(
                float(row["avg_ticket"]) if row["avg_ticket"] is not None else None
            ),
            avg_days_between_tx=(
                float(row["avg_days_between_tx"])
                if row["avg_days_between_tx"] is not None
                else None
            ),
            activity_trend_percentile=(
                float(row["activity_trend_percentile"])
                if row["activity_trend_percentile"] is not None
                else None
            ),
            acquisition_cost_percentile=(
                float(row["acquisition_cost_percentile"])
                if row["acquisition_cost_percentile"] is not None
                else None
            ),
            recency_percentile=(
                float(row["recency_percentile"])
                if row["recency_percentile"] is not None
                else None
            ),
            avg_ticket_percentile=(
                float(row["avg_ticket_percentile"])
                if row["avg_ticket_percentile"] is not None
                else None
            ),
            avg_days_between_tx_percentile=(
                float(row["avg_days_between_tx_percentile"])
                if row["avg_days_between_tx_percentile"] is not None
                else None
            ),
        )

    async def sample_customers(self, per_cluster: int) -> list[CustomerSummary]:
        sql = text("""
            (
                SELECT cr.customer_id, cr.name, cr.email, cr.age, cr.state,
                       ca.cluster_name, ca.lifecycle_stage, ca.rfm_score, ca.recency_days
                FROM customer_analysis ca
                JOIN customers_raw cr ON cr.customer_id = ca.customer_id::uuid
                WHERE ca.cluster_name = 'high_value_active'
                ORDER BY RANDOM() LIMIT :n
            )
            UNION ALL
            (
                SELECT cr.customer_id, cr.name, cr.email, cr.age, cr.state,
                       ca.cluster_name, ca.lifecycle_stage, ca.rfm_score, ca.recency_days
                FROM customer_analysis ca
                JOIN customers_raw cr ON cr.customer_id = ca.customer_id::uuid
                WHERE ca.cluster_name = 'at_risk_churner'
                ORDER BY RANDOM() LIMIT :n
            )
            UNION ALL
            (
                SELECT cr.customer_id, cr.name, cr.email, cr.age, cr.state,
                       ca.cluster_name, ca.lifecycle_stage, ca.rfm_score, ca.recency_days
                FROM customer_analysis ca
                JOIN customers_raw cr ON cr.customer_id = ca.customer_id::uuid
                WHERE ca.cluster_name = 'low_value_dormant'
                ORDER BY RANDOM() LIMIT :n
            )
        """)
        async with self._engine.connect() as conn:
            result = await conn.execute(sql, {"n": per_cluster})
            return [CustomerSummary(**dict(row._mapping)) for row in result]

    async def get_activity_timeline(
        self, customer_id: uuid.UUID
    ) -> list[ActivityTimelineEntry]:
        sql = text("""
            SELECT
                TO_CHAR(DATE_TRUNC('month', transaction_datetime), 'YYYY-MM') AS year_month,
                COUNT(*)::int AS tx_count,
                SUM(amount)::float AS total_amount
            FROM transactions_raw
            WHERE customer_id = :customer_id
            GROUP BY DATE_TRUNC('month', transaction_datetime)
            ORDER BY DATE_TRUNC('month', transaction_datetime)
        """)
        async with self._engine.connect() as conn:
            result = await conn.execute(sql, {"customer_id": str(customer_id)})
            return [ActivityTimelineEntry(**dict(row._mapping)) for row in result]


def get_customer_repository(
    engine: AsyncEngine = Depends(get_engine),
) -> CustomerRepository:
    from fintech_ai_segmentation.app.main import get_aggregate_cache

    return CustomerRepository(engine, get_aggregate_cache())
