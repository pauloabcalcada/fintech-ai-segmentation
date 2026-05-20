from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from fintech_ai_segmentation.app.main import app
from fintech_ai_segmentation.app.repositories.customer import get_customer_repository
from fintech_ai_segmentation.app.schemas.customer import CustomerSummary

client = TestClient(app)

# ---------------------------------------------------------------------------
# Shared stub data — one customer per cluster
# ---------------------------------------------------------------------------

_STUB_SAMPLE = [
    CustomerSummary(
        customer_id="00000000-0000-0000-0000-000000000001",
        name="Alice",
        email="alice@example.com",
        age=30,
        state="SP",
        cluster_name="high_value_active",
        lifecycle_stage="active",
        rfm_score=4.5,
        recency_days=10,
    ),
    CustomerSummary(
        customer_id="00000000-0000-0000-0000-000000000002",
        name="Bob",
        email="bob@example.com",
        age=45,
        state="RJ",
        cluster_name="at_risk_churner",
        lifecycle_stage="at_risk",
        rfm_score=1.2,
        recency_days=90,
    ),
    CustomerSummary(
        customer_id="00000000-0000-0000-0000-000000000003",
        name="Carol",
        email="carol@example.com",
        age=28,
        state="MG",
        cluster_name="low_value_dormant",
        lifecycle_stage="active",
        rfm_score=2.1,
        recency_days=45,
    ),
]


class StubRepo:
    def __init__(self, rows: list[CustomerSummary] | None = None) -> None:
        self._rows = rows if rows is not None else _STUB_SAMPLE

    async def list_customers(self, **_kwargs):
        return [], 0

    async def get_customer_profile(self, customer_id):
        return None

    async def get_activity_timeline(self, customer_id):
        return []

    async def sample_customers(self, per_cluster: int) -> list[CustomerSummary]:
        return self._rows


def _override(rows: list[CustomerSummary] | None = None):
    repo = StubRepo(rows)
    return lambda: repo


# ---------------------------------------------------------------------------
# Cycle 1 — tracer bullet: 200 + envelope shape
# ---------------------------------------------------------------------------


def test_sample_returns_200_with_envelope_shape() -> None:
    app.dependency_overrides[get_customer_repository] = _override()
    try:
        response = client.get("/customers/sample")
        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) >= {"data", "total", "page", "page_size"}
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Cycle 2 — per_cluster=6 is rejected with 422
# ---------------------------------------------------------------------------


def test_sample_rejects_per_cluster_above_max() -> None:
    app.dependency_overrides[get_customer_repository] = _override()
    try:
        response = client.get("/customers/sample?per_cluster=6")
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Cycle 3 — all three cluster names are present in the default response
# ---------------------------------------------------------------------------


def test_sample_contains_all_three_clusters() -> None:
    app.dependency_overrides[get_customer_repository] = _override()
    try:
        response = client.get("/customers/sample")
        assert response.status_code == 200
        cluster_names = {row["cluster_name"] for row in response.json()["data"]}
        assert cluster_names == {"high_value_active", "at_risk_churner", "low_value_dormant"}
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Cycle 4 — per_cluster=3 yields at most 9 rows (3 clusters × 3)
# ---------------------------------------------------------------------------


def test_sample_per_cluster_3_returns_at_most_9_rows() -> None:
    nine_rows = _STUB_SAMPLE * 3  # 9 rows, 3 per cluster
    app.dependency_overrides[get_customer_repository] = _override(nine_rows)
    try:
        response = client.get("/customers/sample?per_cluster=3")
        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) <= 9
        assert body["total"] <= 9
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Cycle 5 — every row in the response has a non-null cluster_name
# ---------------------------------------------------------------------------


def test_sample_every_row_has_non_null_cluster_name() -> None:
    app.dependency_overrides[get_customer_repository] = _override()
    try:
        response = client.get("/customers/sample")
        assert response.status_code == 200
        for row in response.json()["data"]:
            assert row["cluster_name"] is not None
    finally:
        app.dependency_overrides.clear()
