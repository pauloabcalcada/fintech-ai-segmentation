from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from fintech_ai_segmentation.app.main import app
from fintech_ai_segmentation.app.repositories.dashboard import (
    DashboardRepository,
    get_dashboard_repository,
)
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

client = TestClient(app)

# ---------------------------------------------------------------------------
# Stub data
# ---------------------------------------------------------------------------

_STUB_SUMMARY = DashboardSummaryResponse(
    kpi_cards=KpiCards(
        total_customers=8000,
        by_cluster=[
            SegmentBreakdown(cluster_name="high_value_active", customer_count=2500),
            SegmentBreakdown(cluster_name="mid_value_regular", customer_count=3000),
            SegmentBreakdown(cluster_name="at_risk_churner", customer_count=2500),
        ],
        avg_rfm_score=2.8,
        at_risk_count=1500,
    ),
    acquisition_cost_by_channel=[
        AcquisitionCostByChannel(acquisition_channel="organic", avg_acquisition_cost=50.0),
        AcquisitionCostByChannel(acquisition_channel="paid_ads", avg_acquisition_cost=210.0),
        AcquisitionCostByChannel(acquisition_channel="referral", avg_acquisition_cost=30.0),
        AcquisitionCostByChannel(acquisition_channel="partnership", avg_acquisition_cost=120.0),
    ],
    population_by_products_owned=[
        PopulationByProductsOwned(products_owned_count=1, customer_count=3200),
        PopulationByProductsOwned(products_owned_count=2, customer_count=2800),
        PopulationByProductsOwned(products_owned_count=3, customer_count=1200),
    ],
    product_ownership_vs_tenure=[
        ProductOwnershipVsTenure(tenure_bucket="0-6m", avg_products_owned=1.2),
        ProductOwnershipVsTenure(tenure_bucket="6-12m", avg_products_owned=1.8),
        ProductOwnershipVsTenure(tenure_bucket="12-24m", avg_products_owned=2.3),
        ProductOwnershipVsTenure(tenure_bucket="24m+", avg_products_owned=2.9),
    ],
    most_common_products=[
        MostCommonProduct(product_type="wallet", ownership_count=7500),
        MostCommonProduct(product_type="credit_card", ownership_count=4200),
        MostCommonProduct(product_type="investment", ownership_count=2100),
        MostCommonProduct(product_type="insurance", ownership_count=1800),
        MostCommonProduct(product_type="loan", ownership_count=900),
    ],
)

_STUB_AGGREGATES = DashboardAggregatesResponse(
    cohort_activity_matrix=[
        CohortActivityEntry(
            cohort_month="2023-01",
            activity_month="2023-05",
            active_rate=0.52,
            cohort_size=276,
        ),
        CohortActivityEntry(
            cohort_month="2023-01",
            activity_month="2023-06",
            active_rate=0.48,
            cohort_size=276,
        ),
    ],
    channel_m6_retention=[
        ChannelM6RetentionEntry(
            acquisition_channel="referral",
            cohort_month="2023-01",
            m6_active_rate=0.71,
            cohort_size=120,
        ),
        ChannelM6RetentionEntry(
            acquisition_channel="paid_ads",
            cohort_month="2023-01",
            m6_active_rate=0.44,
            cohort_size=88,
        ),
    ],
)


class StubDashboard:
    async def get_summary(self) -> DashboardSummaryResponse:
        return _STUB_SUMMARY

    async def get_aggregates(self) -> DashboardAggregatesResponse:
        return _STUB_AGGREGATES


def _override_dashboard():
    app.dependency_overrides[get_dashboard_repository] = lambda: StubDashboard()


def _clear():
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Cycle 1 — tracer bullet: /dashboard/summary returns 200 with 5 keys
# ---------------------------------------------------------------------------


def test_dashboard_summary_returns_envelope_with_five_keys() -> None:
    _override_dashboard()
    try:
        response = client.get("/dashboard/summary")
        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) == {
            "kpi_cards",
            "acquisition_cost_by_channel",
            "population_by_products_owned",
            "product_ownership_vs_tenure",
            "most_common_products",
        }
    finally:
        _clear()


# ---------------------------------------------------------------------------
# Cycle 2 — kpi_cards has correct shape
# ---------------------------------------------------------------------------


def test_dashboard_summary_kpi_cards_shape() -> None:
    _override_dashboard()
    try:
        response = client.get("/dashboard/summary")
        kpi = response.json()["kpi_cards"]
        assert kpi["total_customers"] == 8000
        assert kpi["avg_rfm_score"] == pytest.approx(2.8)
        assert kpi["at_risk_count"] == 1500
        clusters = {c["cluster_name"] for c in kpi["by_cluster"]}
        assert "high_value_active" in clusters
        assert "at_risk_churner" in clusters
    finally:
        _clear()


# ---------------------------------------------------------------------------
# Cycle 3 — acquisition_cost_by_channel is a list with channel + avg_cost
# ---------------------------------------------------------------------------


def test_dashboard_summary_acquisition_cost_shape() -> None:
    _override_dashboard()
    try:
        response = client.get("/dashboard/summary")
        rows = response.json()["acquisition_cost_by_channel"]
        assert isinstance(rows, list)
        assert len(rows) > 0
        first = rows[0]
        assert "acquisition_channel" in first
        assert "avg_acquisition_cost" in first
    finally:
        _clear()


# ---------------------------------------------------------------------------
# Cycle 4 — population_by_products_owned is a list with products_count + count
# ---------------------------------------------------------------------------


def test_dashboard_summary_population_by_products_owned_shape() -> None:
    _override_dashboard()
    try:
        response = client.get("/dashboard/summary")
        rows = response.json()["population_by_products_owned"]
        assert isinstance(rows, list)
        assert len(rows) > 0
        first = rows[0]
        assert "products_owned_count" in first
        assert "customer_count" in first
    finally:
        _clear()


# ---------------------------------------------------------------------------
# Cycle 5 — product_ownership_vs_tenure has tenure_bucket + avg_products_owned
# ---------------------------------------------------------------------------


def test_dashboard_summary_product_ownership_vs_tenure_shape() -> None:
    _override_dashboard()
    try:
        response = client.get("/dashboard/summary")
        rows = response.json()["product_ownership_vs_tenure"]
        assert isinstance(rows, list)
        assert len(rows) > 0
        buckets = [r["tenure_bucket"] for r in rows]
        assert "0-6m" in buckets
        assert "24m+" in buckets
        assert "avg_products_owned" in rows[0]
    finally:
        _clear()


# ---------------------------------------------------------------------------
# Cycle 6 — most_common_products is a list with product_type + ownership_count
# ---------------------------------------------------------------------------


def test_dashboard_summary_most_common_products_shape() -> None:
    _override_dashboard()
    try:
        response = client.get("/dashboard/summary")
        rows = response.json()["most_common_products"]
        assert isinstance(rows, list)
        assert len(rows) == 5
        product_types = {r["product_type"] for r in rows}
        assert product_types == {"wallet", "credit_card", "investment", "insurance", "loan"}
    finally:
        _clear()


# ---------------------------------------------------------------------------
# Cycle 7 — /dashboard/aggregates returns 200 with 2 keys (tracer)
# ---------------------------------------------------------------------------


def test_dashboard_aggregates_returns_envelope_with_two_keys() -> None:
    _override_dashboard()
    try:
        response = client.get("/dashboard/aggregates")
        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) == {"cohort_activity_matrix", "channel_m6_retention"}
    finally:
        _clear()


# ---------------------------------------------------------------------------
# Cycle 8 — cohort_activity_matrix rows have correct shape
# ---------------------------------------------------------------------------


def test_dashboard_aggregates_cohort_matrix_shape() -> None:
    _override_dashboard()
    try:
        response = client.get("/dashboard/aggregates")
        rows = response.json()["cohort_activity_matrix"]
        assert isinstance(rows, list)
        assert len(rows) > 0
        first = rows[0]
        assert "cohort_month" in first
        assert "activity_month" in first
        assert "active_rate" in first
        assert "cohort_size" in first
    finally:
        _clear()


# ---------------------------------------------------------------------------
# Cycle 9 — channel_m6_retention rows have correct shape
# ---------------------------------------------------------------------------


def test_dashboard_aggregates_channel_retention_shape() -> None:
    _override_dashboard()
    try:
        response = client.get("/dashboard/aggregates")
        rows = response.json()["channel_m6_retention"]
        assert isinstance(rows, list)
        assert len(rows) > 0
        first = rows[0]
        assert "acquisition_channel" in first
        assert "cohort_month" in first
        assert "m6_active_rate" in first
        assert "cohort_size" in first
    finally:
        _clear()
