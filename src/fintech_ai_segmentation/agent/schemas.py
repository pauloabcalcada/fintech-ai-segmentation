"""Pydantic output schema for the LangGraph recommendation agent.

A single model, ``RecommendationOutput``, is the contract between the LLM
response and the rest of the application. Every field is validated by Pydantic
before the recommendation reaches the API caller, so the frontend always
receives a well-typed object even if the LLM returns unexpected values.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class RecommendationOutput(BaseModel):
    risk_level: Literal["low", "medium", "high", "critical"]
    recommended_action: str
    suggested_product: str
    message_tone: str
    reasoning: str
    strategy_used: Literal["retention", "upsell", "reactivation", "activation"]
    notification_text: str
