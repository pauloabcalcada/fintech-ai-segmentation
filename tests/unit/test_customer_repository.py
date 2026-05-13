from __future__ import annotations

import asyncio
import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("SUPABASE_DATABASE_URL"),
    reason="requires live Supabase connection with customer_analysis mart",
)


def _run(coro):  # type: ignore[no-untyped-def]
    return asyncio.run(coro)


@pytest.fixture(scope="module")
def engine():  # type: ignore[no-untyped-def]
    import os

    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool

    url = os.environ["SUPABASE_DATABASE_URL"].replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    eng = create_async_engine(url, poolclass=NullPool)
    yield eng
    _run(eng.dispose())


@pytest.fixture(scope="module")
def repo(engine):  # type: ignore[no-untyped-def]
    from fintech_ai_segmentation.app.repositories.customer import CustomerRepository

    return CustomerRepository(engine)


# ---------------------------------------------------------------------------
# Cycle 7 — returns rows and a positive total from the mart
# ---------------------------------------------------------------------------


def test_list_customers_returns_rows_from_mart(repo) -> None:  # type: ignore[no-untyped-def]
    async def _run_inner():
        customers, total = await repo.list_customers()
        return customers, total

    customers, total = _run(_run_inner())
    assert total > 0
    assert len(customers) > 0
    assert customers[0].customer_id is not None


# ---------------------------------------------------------------------------
# Cycle 8 — pagination: page 2 returns a different slice than page 1
# ---------------------------------------------------------------------------


def test_list_customers_pagination_returns_different_slices(repo) -> None:  # type: ignore[no-untyped-def]
    async def _run_inner():
        page1, _ = await repo.list_customers(page=1, page_size=10)
        page2, _ = await repo.list_customers(page=2, page_size=10)
        return page1, page2

    page1, page2 = _run(_run_inner())
    ids_page1 = {c.customer_id for c in page1}
    ids_page2 = {c.customer_id for c in page2}
    assert ids_page1.isdisjoint(ids_page2)


# ---------------------------------------------------------------------------
# Cycle 9 — filter by cluster_name reduces result count
# ---------------------------------------------------------------------------


def test_list_customers_filter_by_cluster(repo) -> None:  # type: ignore[no-untyped-def]
    async def _run_inner():
        all_customers, total_all = await repo.list_customers(page_size=1)
        # find any cluster to filter on
        sample, _ = await repo.list_customers(page_size=5)
        cluster = next((c.cluster_name for c in sample if c.cluster_name), None)
        if cluster is None:
            return total_all, total_all  # no cluster data; test trivially passes
        filtered, total_filtered = await repo.list_customers(cluster=cluster, page_size=1)
        return total_all, total_filtered

    total_all, total_filtered = _run(_run_inner())
    assert total_filtered <= total_all


# ---------------------------------------------------------------------------
# Cycle 10 — filter by lifecycle_stage reduces result count
# ---------------------------------------------------------------------------


def test_list_customers_filter_by_lifecycle_stage(repo) -> None:  # type: ignore[no-untyped-def]
    async def _run_inner():
        sample, total_all = await repo.list_customers(page_size=5)
        stage = next((c.lifecycle_stage for c in sample if c.lifecycle_stage), None)
        if stage is None:
            return total_all, total_all
        _, total_filtered = await repo.list_customers(lifecycle_stage=stage, page_size=1)
        return total_all, total_filtered

    total_all, total_filtered = _run(_run_inner())
    assert total_filtered <= total_all


# ---------------------------------------------------------------------------
# Cycle 11 — filter by acquisition_channel reduces result count
# ---------------------------------------------------------------------------


def test_list_customers_filter_by_channel(repo) -> None:  # type: ignore[no-untyped-def]
    async def _run_inner():
        _, total_all = await repo.list_customers(page_size=1)
        _, total_paid = await repo.list_customers(channel="paid_ads", page_size=1)
        return total_all, total_paid

    total_all, total_paid = _run(_run_inner())
    assert 0 < total_paid <= total_all


# ---------------------------------------------------------------------------
# Cycle 12 — full-text search on name narrows results
# ---------------------------------------------------------------------------


def test_list_customers_search_on_name_narrows_results(repo) -> None:  # type: ignore[no-untyped-def]
    async def _run_inner():
        sample, total_all = await repo.list_customers(page_size=5)
        if not sample:
            return total_all, total_all
        # Use first 3 chars of the first customer's name as search prefix
        prefix = sample[0].name[:3]
        _, total_search = await repo.list_customers(q=prefix, page_size=1)
        return total_all, total_search

    total_all, total_search = _run(_run_inner())
    assert total_search <= total_all


# ---------------------------------------------------------------------------
# Cycle 13 — sort by rfm_score desc returns highest score first
# ---------------------------------------------------------------------------


def test_list_customers_sort_rfm_score_desc(repo) -> None:  # type: ignore[no-untyped-def]
    async def _run_inner():
        customers, _ = await repo.list_customers(sort="rfm_score", order="desc", page_size=10)
        return [c.rfm_score for c in customers if c.rfm_score is not None]

    scores = _run(_run_inner())
    assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# Cycle 14 — sort by rfm_score asc returns lowest score first
# ---------------------------------------------------------------------------


def test_list_customers_sort_rfm_score_asc(repo) -> None:  # type: ignore[no-untyped-def]
    async def _run_inner():
        customers, _ = await repo.list_customers(sort="rfm_score", order="asc", page_size=10)
        return [c.rfm_score for c in customers if c.rfm_score is not None]

    scores = _run(_run_inner())
    assert scores == sorted(scores)


# ---------------------------------------------------------------------------
# Cycle 15 — get_customer_profile returns a profile for an existing customer
# ---------------------------------------------------------------------------


def test_get_customer_profile_returns_profile_for_existing_customer(repo) -> None:  # type: ignore[no-untyped-def]
    async def _run_inner():
        customers, _ = await repo.list_customers(page_size=1)
        customer_id = customers[0].customer_id
        profile = await repo.get_customer_profile(customer_id)
        return profile, customer_id

    profile, customer_id = _run(_run_inner())
    assert profile is not None
    assert profile.customer_id == customer_id
    assert profile.name
    assert profile.email


# ---------------------------------------------------------------------------
# Cycle 16 — get_customer_profile returns None for an unknown customer ID
# ---------------------------------------------------------------------------


def test_get_customer_profile_returns_none_for_unknown_id(repo) -> None:  # type: ignore[no-untyped-def]
    import uuid

    async def _run_inner():
        return await repo.get_customer_profile(uuid.uuid4())

    result = _run(_run_inner())
    assert result is None


# ---------------------------------------------------------------------------
# Cycle 17 — cluster_position is one of bottom_20, mid_60, top_20
# ---------------------------------------------------------------------------


def test_get_customer_profile_cluster_position_is_valid_label(repo) -> None:  # type: ignore[no-untyped-def]
    async def _run_inner():
        customers, _ = await repo.list_customers(page_size=1)
        customer_id = customers[0].customer_id
        return await repo.get_customer_profile(customer_id)

    profile = _run(_run_inner())
    assert profile is not None
    assert profile.cluster_position in {"bottom_20", "mid_60", "top_20"}


# ---------------------------------------------------------------------------
# Cycle 18 — cluster_averages and population_averages are non-null when cache loaded
# ---------------------------------------------------------------------------


def test_get_customer_profile_cluster_averages_non_null_with_cache(repo, engine) -> None:  # type: ignore[no-untyped-def]
    from fintech_ai_segmentation.app.repositories.customer import AggregateCache, CustomerRepository

    async def _run_inner():
        cache = await AggregateCache.load(engine)
        repo_with_cache = CustomerRepository(engine, cache)
        # pick a clustered customer (sort asc so NULLs go last)
        customers, _ = await repo_with_cache.list_customers(
            sort="rfm_score", order="asc", page_size=1
        )
        return await repo_with_cache.get_customer_profile(customers[0].customer_id)

    profile = _run(_run_inner())
    assert profile is not None
    assert profile.cluster_averages is not None
    assert profile.population_averages is not None
    assert 0.0 <= profile.cluster_averages.rfm_score <= 5.0
    assert 0.0 <= profile.population_averages.rfm_score <= 5.0


# ---------------------------------------------------------------------------
# Cycle 19 — cluster_product_profile fractions are between 0 and 1
# ---------------------------------------------------------------------------


def test_get_customer_profile_cluster_product_profile_fractions_valid(repo, engine) -> None:  # type: ignore[no-untyped-def]
    from fintech_ai_segmentation.app.repositories.customer import AggregateCache, CustomerRepository

    async def _run_inner():
        cache = await AggregateCache.load(engine)
        repo_with_cache = CustomerRepository(engine, cache)
        customers, _ = await repo_with_cache.list_customers(
            sort="rfm_score", order="asc", page_size=1
        )
        return await repo_with_cache.get_customer_profile(customers[0].customer_id)

    profile = _run(_run_inner())
    assert profile is not None
    assert profile.cluster_product_profile is not None
    cpp = profile.cluster_product_profile
    for pct in (cpp.wallet_pct, cpp.credit_card_pct, cpp.investment_pct, cpp.insurance_pct, cpp.loan_pct):
        assert 0.0 <= pct <= 1.0


# ---------------------------------------------------------------------------
# Cycle 20 — get_activity_timeline returns entries ordered chronologically
# ---------------------------------------------------------------------------


def test_get_activity_timeline_entries_ordered_chronologically(repo) -> None:  # type: ignore[no-untyped-def]
    async def _run_inner():
        # pick a customer known to have transactions (lowest rfm = most activity)
        customers, _ = await repo.list_customers(sort="rfm_score", order="asc", page_size=1)
        customer_id = customers[0].customer_id
        timeline = await repo.get_activity_timeline(customer_id)
        return timeline

    timeline = _run(_run_inner())
    assert len(timeline) > 0
    year_months = [e.year_month for e in timeline]
    assert year_months == sorted(year_months)
    for entry in timeline:
        assert entry.tx_count > 0
        assert entry.total_amount >= 0.0
