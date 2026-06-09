from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from fintech_ai_segmentation.app.main import app
from fintech_ai_segmentation.app.repositories.customer import get_customer_repository
from fintech_ai_segmentation.app.repositories.recommendation import (
    Allowed,
    Blocked,
    CachedResult,
    get_rate_limiter,
    get_recommendation_agent,
    get_recommendation_log_store,
)
from fintech_ai_segmentation.app.schemas.customer import (
    ClusterProductProfile,
    CustomerProfile,
    RFMAverages,
)
from fintech_ai_segmentation.agent.schemas import RecommendationOutput

client = TestClient(app)

_CUSTOMER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

_STUB_PROFILE = CustomerProfile(
    customer_id=_CUSTOMER_ID,
    name="Alice",
    email="alice@example.com",
    age=30,
    state="SP",
    acquisition_channel="organic",
    acquisition_cost=50.0,
    registration_date="2024-01-01",
    tenure_months=12,
    cluster_name="at_risk_churner",
    lifecycle_stage="active",
    rfm_score=1.4,
    recency_score=1.0,
    frequency_score=1.0,
    monetary_score=1.0,
    recency_days=92,
    products_owned_count=1,
    has_wallet=True,
    has_credit_card=False,
    has_investment=False,
    has_insurance=False,
    has_loan=False,
    cluster_position="mid_60",
    cluster_averages=RFMAverages(
        recency_score=1.5, frequency_score=1.5, monetary_score=1.5, rfm_score=1.5
    ),
    population_averages=RFMAverages(
        recency_score=3.0, frequency_score=3.0, monetary_score=3.0, rfm_score=3.0
    ),
    cluster_product_profile=ClusterProductProfile(
        wallet_pct=0.9,
        credit_card_pct=0.1,
        investment_pct=0.1,
        insurance_pct=0.1,
        loan_pct=0.1,
    ),
)


class StubRepo:
    def __init__(self, profile=_STUB_PROFILE):
        self._profile = profile

    async def list_customers(self, **_kwargs):
        return [], 0

    async def get_customer_profile(self, customer_id):
        if self._profile and self._profile.customer_id == customer_id:
            return self._profile
        return None

    async def get_activity_timeline(self, customer_id):
        return []


def _repo_override(profile=_STUB_PROFILE):
    repo = StubRepo(profile)
    return lambda: repo


_STUB_RECOMMENDATION = RecommendationOutput(
    risk_level="critical",
    recommended_action="immediate retention offer",
    suggested_product="cashback credit card",
    message_tone="urgent, empathetic",
    reasoning="Customer is at risk.",
    strategy_used="retention",
    notification_text="We miss you! Come back and get a special offer today.",
)

_STUB_RECOMMENDATION_JSON = _STUB_RECOMMENDATION.model_dump()


class StubAgent:
    def __init__(self, result=_STUB_RECOMMENDATION):
        self._result = result

    async def run(self, customer_id, model_id="smart-auto", language="en"):
        return self._result


class StubRateLimiter:
    def __init__(self, result=None):
        self._result = result if result is not None else Allowed()
        self.checked = []

    async def check(self, customer_id, ip_address, language="en"):
        self.checked.append((customer_id, ip_address, language))
        return self._result


class StubLogStore:
    def __init__(self):
        self.recorded = []

    async def record(
        self, customer_id, ip_address, model_used, recommendation_json, language="en"
    ):
        self.recorded.append(
            (customer_id, ip_address, model_used, recommendation_json, language)
        )

    async def get_cached_recommendation(self, customer_id, language="en"):
        return None


def _all_overrides(profile=_STUB_PROFILE, rate_result=None, log_store=None, agent=None):
    stub_log = log_store or StubLogStore()
    stub_agent = agent or StubAgent()
    stub_limiter = StubRateLimiter(rate_result)
    return {
        get_customer_repository: _repo_override(profile),
        get_rate_limiter: lambda: stub_limiter,
        get_recommendation_log_store: lambda: stub_log,
        get_recommendation_agent: lambda: stub_agent,
    }, stub_log


# ---------------------------------------------------------------------------
# Cycle 0 — POST with no model field → 200 (model is hardcoded server-side)
# ---------------------------------------------------------------------------


def test_analyze_no_model_field_returns_200() -> None:
    overrides, _ = _all_overrides()
    app.dependency_overrides.update(overrides)
    try:
        response = client.post(
            f"/customers/{_CUSTOMER_ID}/analyze",
            json={},
        )
        assert response.status_code == 200
        assert response.json()["recommendation"]["risk_level"] == "critical"
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Cycle 1 — no password required → analyze succeeds without any auth header
# ---------------------------------------------------------------------------


def test_analyze_requires_no_password() -> None:
    overrides, _ = _all_overrides()
    app.dependency_overrides.update(overrides)
    try:
        response = client.post(
            f"/customers/{_CUSTOMER_ID}/analyze",
            json={},
        )
        assert response.status_code == 200
        assert response.json()["recommendation"]["risk_level"] == "critical"
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Cycle 2 — Allowed → agent called, recommendation returned with cached=false
# ---------------------------------------------------------------------------


def test_analyze_allowed_returns_recommendation() -> None:
    overrides, stub_log = _all_overrides(rate_result=Allowed())
    app.dependency_overrides.update(overrides)
    try:
        response = client.post(
            f"/customers/{_CUSTOMER_ID}/analyze",
            json={},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["cached"] is False
        assert body["recommendation"]["risk_level"] == "critical"
        assert (
            body["recommendation"]["recommended_action"] == "immediate retention offer"
        )
        assert len(stub_log.recorded) == 1
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Cycle 3 — CachedResult → returns cached data, agent is never called
# ---------------------------------------------------------------------------


def test_analyze_cached_returns_cached_recommendation() -> None:
    cached_at = datetime(2026, 5, 14, 10, 0, 0, tzinfo=timezone.utc)
    cached_result = CachedResult(
        recommendation_json=_STUB_RECOMMENDATION_JSON,
        generated_at=cached_at,
        model_used="llama-70b-free",
    )

    class NeverCalledAgent:
        async def run(self, customer_id, model_id="smart-auto", language="en"):
            raise AssertionError("Agent should not be called for cached result")

    overrides, stub_log = _all_overrides(
        rate_result=cached_result, agent=NeverCalledAgent()
    )
    app.dependency_overrides.update(overrides)
    try:
        response = client.post(
            f"/customers/{_CUSTOMER_ID}/analyze",
            json={},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["cached"] is True
        assert body["model_used"] == "llama-70b-free"
        assert body["recommendation"]["risk_level"] == "critical"
        assert len(stub_log.recorded) == 0
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Cycle 4 — Blocked → HTTP 429 with retry_after
# ---------------------------------------------------------------------------


def test_analyze_blocked_returns_429_with_retry_after() -> None:
    retry_at = datetime(2026, 5, 15, 10, 0, 0, tzinfo=timezone.utc)
    overrides, _ = _all_overrides(rate_result=Blocked(retry_after=retry_at))
    app.dependency_overrides.update(overrides)
    try:
        response = client.post(
            f"/customers/{_CUSTOMER_ID}/analyze",
            json={},
        )
        assert response.status_code == 429
        body = response.json()
        assert body["detail"]["error"] == "rate_limit_exceeded"
        assert "2026-05-15" in body["detail"]["retry_after"]
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Cycle 5 — unknown customer → 404
# ---------------------------------------------------------------------------


def test_analyze_unknown_customer_returns_404() -> None:
    unknown_id = uuid.UUID("00000000-0000-0000-0000-000000000099")
    overrides, _ = _all_overrides(profile=None)
    app.dependency_overrides.update(overrides)
    try:
        response = client.post(
            f"/customers/{unknown_id}/analyze",
            json={},
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Cycle 6 — unsupported language → 422
# ---------------------------------------------------------------------------


def test_analyze_language_forwarded_to_agent() -> None:
    received: list[str] = []

    class CapturingAgent:
        async def run(self, customer_id, model_id="smart-auto", language="en"):
            received.append(language)
            return _STUB_RECOMMENDATION

    overrides, _ = _all_overrides(agent=CapturingAgent())
    app.dependency_overrides.update(overrides)
    try:
        client.post(
            f"/customers/{_CUSTOMER_ID}/analyze",
            json={"language": "pt-BR"},
        )
        assert received == ["pt-BR"]
    finally:
        app.dependency_overrides.clear()


def test_analyze_pt_br_language_returns_200() -> None:
    overrides, _ = _all_overrides()
    app.dependency_overrides.update(overrides)
    try:
        response = client.post(
            f"/customers/{_CUSTOMER_ID}/analyze",
            json={"language": "pt-BR"},
        )
        assert response.status_code == 200
        assert response.json()["recommendation"]["risk_level"] == "critical"
    finally:
        app.dependency_overrides.clear()


def test_analyze_uses_forwarded_client_ip_for_rate_limiting() -> None:
    stub_limiter = StubRateLimiter(Allowed())
    app.dependency_overrides.update(
        {
            get_customer_repository: _repo_override(),
            get_rate_limiter: lambda: stub_limiter,
            get_recommendation_log_store: lambda: StubLogStore(),
            get_recommendation_agent: lambda: StubAgent(),
        }
    )
    try:
        response = client.post(
            f"/customers/{_CUSTOMER_ID}/analyze",
            json={},
            headers={"X-Forwarded-For": "203.0.113.42, 10.0.0.5"},
        )
        assert response.status_code == 200
        # The real client (rightmost, appended by the trusted proxy) must be
        # used — not the spoofable leading entry, nor the proxy peer.
        assert stub_limiter.checked[0][1] == "10.0.0.5"
    finally:
        app.dependency_overrides.clear()


def test_analyze_unsupported_language_returns_422() -> None:
    overrides, _ = _all_overrides()
    app.dependency_overrides.update(overrides)
    try:
        response = client.post(
            f"/customers/{_CUSTOMER_ID}/analyze",
            json={"language": "fr"},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
