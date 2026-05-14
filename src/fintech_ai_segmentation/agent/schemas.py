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
