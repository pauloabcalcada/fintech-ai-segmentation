from __future__ import annotations

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from fintech_ai_segmentation.app.database import get_engine
from fintech_ai_segmentation.app.schemas.customer import CustomerSummary

_SORT_ALLOWLIST = {"rfm_score", "recency_days", "monetary_total"}
_SEARCH_MAX_LEN = 100

_BASE_FROM = """
    FROM customer_analysis ca
    JOIN customers_raw cr ON cr.customer_id = ca.customer_id::uuid
"""


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
    """Return a (WHERE clause, params dict) with only active filter conditions."""
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


class CustomerRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

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
            ORDER BY ca.{sort_col} {order_dir}
            LIMIT :limit OFFSET :offset
        """)

        page_params = {**filter_params, "limit": page_size, "offset": offset}

        async with self._engine.connect() as conn:
            total: int = (await conn.execute(count_sql, filter_params)).scalar_one()
            result = await conn.execute(rows_sql, page_params)
            customers = [CustomerSummary(**dict(row._mapping)) for row in result]

        return customers, total


def get_customer_repository(engine: AsyncEngine = Depends(get_engine)) -> CustomerRepository:
    return CustomerRepository(engine)
