from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from fintech_ai_segmentation.app.main import app
from fintech_ai_segmentation.app.repositories.customer import (
    CustomerRepository,
    _build_search_pattern,
    get_customer_repository,
)
from fintech_ai_segmentation.app.schemas.customer import CustomerSummary

client = TestClient(app)

# ---------------------------------------------------------------------------
# Stub repository — returns canned data, no DB needed
# ---------------------------------------------------------------------------

_STUB_CUSTOMERS = [
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
        cluster_name="high_value_active",
        lifecycle_stage="active",
        rfm_score=4.8,
        recency_days=5,
    ),
]


class StubRepo:
    def __init__(self, rows: list[CustomerSummary] | None = None, total: int | None = None) -> None:
        self._rows = rows if rows is not None else _STUB_CUSTOMERS
        self._total = total if total is not None else len(self._rows)

    async def list_customers(self, **_kwargs) -> tuple[list[CustomerSummary], int]:  # type: ignore[override]
        return self._rows, self._total


def _override(rows: list[CustomerSummary] | None = None, total: int | None = None):
    repo = StubRepo(rows, total)
    return lambda: repo


# ---------------------------------------------------------------------------
# Cycle 1 — tracer bullet: response envelope shape
# ---------------------------------------------------------------------------


def test_list_customers_returns_envelope_shape() -> None:
    app.dependency_overrides[get_customer_repository] = _override([])
    try:
        response = client.get("/customers")
        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) >= {"data", "total", "page", "page_size"}
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Cycle 2 — default pagination values echo back in response
# ---------------------------------------------------------------------------


def test_list_customers_default_pagination() -> None:
    app.dependency_overrides[get_customer_repository] = _override([])
    try:
        response = client.get("/customers")
        body = response.json()
        assert body["page"] == 1
        assert body["page_size"] == 50
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Cycle 3 — explicit page/page_size are reflected in response
# ---------------------------------------------------------------------------


def test_list_customers_explicit_page_and_size() -> None:
    app.dependency_overrides[get_customer_repository] = _override([])
    try:
        response = client.get("/customers?page=3&page_size=10")
        body = response.json()
        assert body["page"] == 3
        assert body["page_size"] == 10
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Cycle 4 — page_size over 100 is rejected
# ---------------------------------------------------------------------------


def test_list_customers_rejects_page_size_over_100() -> None:
    app.dependency_overrides[get_customer_repository] = _override([])
    try:
        response = client.get("/customers?page_size=101")
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Cycle 5 — data field contains serialised CustomerSummary rows
# ---------------------------------------------------------------------------


def test_list_customers_data_contains_customer_rows() -> None:
    app.dependency_overrides[get_customer_repository] = _override(_STUB_CUSTOMERS)
    try:
        response = client.get("/customers")
        body = response.json()
        assert body["total"] == 3
        first = body["data"][0]
        assert first["name"] == "Alice"
        assert first["cluster_name"] == "high_value_active"
        assert first["rfm_score"] == pytest.approx(4.5)
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Cycle 6 — total reflects count from repository (independent of page_size)
# ---------------------------------------------------------------------------


def test_list_customers_total_comes_from_repository() -> None:
    app.dependency_overrides[get_customer_repository] = _override([], total=999)
    try:
        response = client.get("/customers")
        body = response.json()
        assert body["total"] == 999
        assert body["data"] == []
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Search sanitization — pure unit tests, no DB or HTTP needed
# ---------------------------------------------------------------------------


def test_build_search_pattern_wraps_term_in_wildcards() -> None:
    assert _build_search_pattern("alice") == "%alice%"


def test_build_search_pattern_none_returns_none() -> None:
    assert _build_search_pattern(None) is None


def test_build_search_pattern_empty_string_returns_none() -> None:
    assert _build_search_pattern("") is None


def test_build_search_pattern_truncates_at_100_chars() -> None:
    long_q = "a" * 150
    pattern = _build_search_pattern(long_q)
    assert pattern is not None
    # wildcards add 2 chars; the payload must be capped at 100
    assert len(pattern) == 102
