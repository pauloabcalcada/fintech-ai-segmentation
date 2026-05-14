from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from fintech_ai_segmentation.agent.recommendation_agent import LangGraphRecommendationAgent
from fintech_ai_segmentation.agent.schemas import RecommendationOutput
from fintech_ai_segmentation.app.schemas.customer import CustomerProfile

_CUSTOMER_ID = uuid.uuid4()

_VALID_LLM_RESPONSE = """{
  "risk_level": "high",
  "recommended_action": "Send a personalised re-engagement offer",
  "suggested_product": "cashback credit card",
  "message_tone": "urgent, empathetic",
  "reasoning": "Customer has been inactive for 92 days with RFM score of 1.4, well below the segment average of 2.1. Acquisition cost of R$280 via paid_ads has not yet been recovered."
}"""

_MALFORMED_LLM_RESPONSE = '{"risk_level": "unknown", "recommended_action": ""}'


def _make_profile(cluster_name: str | None, lifecycle_stage: str = "active") -> CustomerProfile:
    return CustomerProfile(
        customer_id=_CUSTOMER_ID,
        name="Test Customer",
        email="test@example.com",
        age=35,
        state="SP",
        acquisition_channel="paid_ads",
        acquisition_cost=280.0,
        registration_date=date(2023, 1, 15),
        tenure_months=16,
        cluster_name=cluster_name,
        lifecycle_stage=lifecycle_stage,
        rfm_score=1.4,
        recency_score=1.0,
        frequency_score=1.0,
        monetary_score=2.0,
        recency_days=92,
        products_owned_count=1,
        has_wallet=True,
        has_credit_card=False,
        has_investment=False,
        has_insurance=False,
        has_loan=False,
        cluster_position="bottom_20",
        cluster_averages=None,
        population_averages=None,
        cluster_product_profile=None,
    )


def _make_agent(cluster_name: str | None, lifecycle_stage: str = "active") -> LangGraphRecommendationAgent:
    repository = MagicMock()
    repository.get_customer_profile = AsyncMock(return_value=_make_profile(cluster_name, lifecycle_stage))
    repository.get_activity_timeline = AsyncMock(return_value=[])

    llm_client = MagicMock()
    llm_client.complete = MagicMock(return_value=_VALID_LLM_RESPONSE)

    return LangGraphRecommendationAgent(llm_client=llm_client, repository=repository)


# --- routing tests ---

async def test_at_risk_churner_routes_to_retention() -> None:
    agent = _make_agent("at_risk_churner")
    result = await agent.run(_CUSTOMER_ID)
    assert result.strategy_used == "retention"


async def test_high_value_active_routes_to_upsell() -> None:
    agent = _make_agent("high_value_active")
    result = await agent.run(_CUSTOMER_ID)
    assert result.strategy_used == "upsell"


async def test_low_value_dormant_routes_to_reactivation() -> None:
    agent = _make_agent("low_value_dormant")
    result = await agent.run(_CUSTOMER_ID)
    assert result.strategy_used == "reactivation"


async def test_no_cluster_routes_to_activation() -> None:
    agent = _make_agent(cluster_name=None)
    result = await agent.run(_CUSTOMER_ID)
    assert result.strategy_used == "activation"


# --- output validation tests ---

async def test_well_formed_llm_response_returns_recommendation_output() -> None:
    agent = _make_agent("at_risk_churner")
    result = await agent.run(_CUSTOMER_ID)
    assert isinstance(result, RecommendationOutput)
    assert result.risk_level == "high"
    assert result.suggested_product == "cashback credit card"


async def test_malformed_llm_response_raises_validation_error() -> None:
    repository = MagicMock()
    repository.get_customer_profile = AsyncMock(return_value=_make_profile("at_risk_churner"))
    repository.get_activity_timeline = AsyncMock(return_value=[])
    llm_client = MagicMock()
    llm_client.complete = MagicMock(return_value=_MALFORMED_LLM_RESPONSE)

    from pydantic import ValidationError
    agent = LangGraphRecommendationAgent(llm_client=llm_client, repository=repository)
    with pytest.raises((ValidationError, Exception)):
        await agent.run(_CUSTOMER_ID)
