from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
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
    ActivityTimelineEntry,
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
    cluster_averages=RFMAverages(recency_score=1.5, frequency_score=1.5, monetary_score=1.5, rfm_score=1.5),
    population_averages=RFMAverages(recency_score=3.0, frequency_score=3.0, monetary_score=3.0, rfm_score=3.0),
    cluster_product_profile=ClusterProductProfile(
        wallet_pct=0.9, credit_card_pct=0.1, investment_pct=0.1, insurance_pct=0.1, loan_pct=0.1
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
)

_STUB_RECOMMENDATION_JSON = _STUB_RECOMMENDATION.model_dump()


class StubAgent:
    def __init__(self, result=_STUB_RECOMMENDATION):
        self._result = result

    async def run(self, customer_id, model_id="smart-auto"):
        return self._result


class StubRateLimiter:
    def __init__(self, result=None):
        self._result = result if result is not None else Allowed()

    async def check(self, customer_id, ip_address):
        return self._result


class StubLogStore:
    def __init__(self):
        self.recorded = []

    async def record(self, customer_id, ip_address, model_used, recommendation_json):
        self.recorded.append((customer_id, ip_address, model_used, recommendation_json))


def _all_overrides(
    profile=_STUB_PROFILE,
    rate_result=None,
    log_store=None,
    agent=None,
    monkeypatch=None,
):
    stub_log = log_store or StubLogStore()
    stub_agent = agent or StubAgent()
    stub_limiter = StubRateLimiter(rate_result)

    overrides = {
        get_customer_repository: _repo_override(profile),
        get_rate_limiter: lambda: stub_limiter,
        get_recommendation_log_store: lambda: stub_log,
        get_recommendation_agent: lambda: stub_agent,
    }
    if monkeypatch:
        monkeypatch.setenv("DEMO_PASSWORD", "secret")
        from fintech_ai_segmentation.app import settings as settings_module
        settings_module.get_settings.cache_clear()
    return overrides, stub_log


_CORRECT_HEADERS = {"X-Demo-Password": "secret"}


# ---------------------------------------------------------------------------
# Cycle 1 — missing X-Demo-Password header → 401
# ---------------------------------------------------------------------------


def test_analyze_without_password_header_returns_401() -> None:
    app.dependency_overrides[get_customer_repository] = _repo_override()
    try:
        response = client.post(
            f"/customers/{_CUSTOMER_ID}/analyze",
            json={"model": "gemini-flash-free"},
        )
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Cycle 2 — wrong X-Demo-Password header → 401
# ---------------------------------------------------------------------------


def test_analyze_with_wrong_password_returns_401() -> None:
    app.dependency_overrides[get_customer_repository] = _repo_override()
    try:
        response = client.post(
            f"/customers/{_CUSTOMER_ID}/analyze",
            json={"model": "gemini-flash-free"},
            headers={"X-Demo-Password": "wrong-password"},
        )
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Cycle 3 — correct password → request is not rejected by auth (not 401)
# ---------------------------------------------------------------------------
# (password correctness is tested against the empty DEMO_PASSWORD default;
#  Cycles 4+ use monkeypatch to set a real value)


def test_analyze_with_correct_password_passes_auth(monkeypatch) -> None:
    from fintech_ai_segmentation.app import settings as settings_module

    overrides, _ = _all_overrides(monkeypatch=monkeypatch)
    app.dependency_overrides.update(overrides)
    try:
        response = client.post(
            f"/customers/{_CUSTOMER_ID}/analyze",
            json={"model": "gemini-flash-free"},
            headers=_CORRECT_HEADERS,
        )
        assert response.status_code != 401
    finally:
        app.dependency_overrides.clear()
        settings_module.get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Cycle 4 — Allowed → agent called, recommendation returned with cached=false
# ---------------------------------------------------------------------------
# Helpers shared across Cycles 4+

def _setup(monkeypatch):
    from fintech_ai_segmentation.app import settings as settings_module
    monkeypatch.setenv("DEMO_PASSWORD", "secret")
    settings_module.get_settings.cache_clear()
    return settings_module


def _teardown(settings_module):
    app.dependency_overrides.clear()
    settings_module.get_settings.cache_clear()


def test_analyze_allowed_returns_recommendation(monkeypatch) -> None:
    from fintech_ai_segmentation.app import settings as settings_module

    monkeypatch.setenv("DEMO_PASSWORD", "secret")
    settings_module.get_settings.cache_clear()

    overrides, stub_log = _all_overrides(rate_result=Allowed())
    app.dependency_overrides.update(overrides)
    try:
        response = client.post(
            f"/customers/{_CUSTOMER_ID}/analyze",
            json={"model": "gemini-flash-free"},
            headers=_CORRECT_HEADERS,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["cached"] is False
        assert body["recommendation"]["risk_level"] == "critical"
        assert body["recommendation"]["recommended_action"] == "immediate retention offer"
        assert len(stub_log.recorded) == 1
    finally:
        app.dependency_overrides.clear()
        settings_module.get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Cycle 5 — CachedResult → returns cached data, no agent call
# ---------------------------------------------------------------------------


def test_analyze_cached_returns_cached_recommendation(monkeypatch) -> None:
    settings_module = _setup(monkeypatch)
    cached_at = datetime(2026, 5, 14, 10, 0, 0, tzinfo=timezone.utc)
    cached_result = CachedResult(
        recommendation_json=_STUB_RECOMMENDATION_JSON,
        generated_at=cached_at,
        model_used="llama-70b-free",
    )

    class NeverCalledAgent:
        async def run(self, *args, **kwargs):
            raise AssertionError("Agent should not be called for cached result")

    overrides, stub_log = _all_overrides(
        rate_result=cached_result,
        agent=NeverCalledAgent(),
    )
    app.dependency_overrides.update(overrides)
    try:
        response = client.post(
            f"/customers/{_CUSTOMER_ID}/analyze",
            json={"model": "gemini-flash-free"},
            headers=_CORRECT_HEADERS,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["cached"] is True
        assert body["model_used"] == "llama-70b-free"
        assert body["recommendation"]["risk_level"] == "critical"
        assert len(stub_log.recorded) == 0
    finally:
        _teardown(settings_module)


# ---------------------------------------------------------------------------
# Cycle 6 — Blocked → HTTP 429 with retry_after
# ---------------------------------------------------------------------------


def test_analyze_blocked_returns_429_with_retry_after(monkeypatch) -> None:
    settings_module = _setup(monkeypatch)
    retry_at = datetime(2026, 5, 15, 10, 0, 0, tzinfo=timezone.utc)
    blocked_result = Blocked(retry_after=retry_at)

    overrides, _ = _all_overrides(rate_result=blocked_result)
    app.dependency_overrides.update(overrides)
    try:
        response = client.post(
            f"/customers/{_CUSTOMER_ID}/analyze",
            json={"model": "smart-auto"},
            headers=_CORRECT_HEADERS,
        )
        assert response.status_code == 429
        body = response.json()
        assert body["detail"]["error"] == "rate_limit_exceeded"
        assert "2026-05-15" in body["detail"]["retry_after"]
    finally:
        _teardown(settings_module)


# ---------------------------------------------------------------------------
# Cycle 7 — unknown customer → 404
# ---------------------------------------------------------------------------


def test_analyze_unknown_customer_returns_404(monkeypatch) -> None:
    settings_module = _setup(monkeypatch)
    unknown_id = uuid.UUID("00000000-0000-0000-0000-000000000099")

    overrides, _ = _all_overrides(profile=None)
    app.dependency_overrides.update(overrides)
    try:
        response = client.post(
            f"/customers/{unknown_id}/analyze",
            json={"model": "gemini-flash-free"},
            headers=_CORRECT_HEADERS,
        )
        assert response.status_code == 404
    finally:
        _teardown(settings_module)


# ---------------------------------------------------------------------------
# Cycle 8 — unknown model string → 422
# ---------------------------------------------------------------------------


def test_analyze_unknown_model_returns_422(monkeypatch) -> None:
    settings_module = _setup(monkeypatch)
    overrides, _ = _all_overrides()
    app.dependency_overrides.update(overrides)
    try:
        response = client.post(
            f"/customers/{_CUSTOMER_ID}/analyze",
            json={"model": "gpt-4o"},
            headers=_CORRECT_HEADERS,
        )
        assert response.status_code == 422
    finally:
        _teardown(settings_module)
