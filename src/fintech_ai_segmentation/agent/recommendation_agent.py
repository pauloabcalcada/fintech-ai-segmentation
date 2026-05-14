from __future__ import annotations

import json
import uuid
from typing import TypedDict

from langgraph.graph import END, StateGraph

from fintech_ai_segmentation.agent.llm_client import OpenRouterLLMClient
from fintech_ai_segmentation.agent.prompts import (
    ACTIVATION_SYSTEM,
    REACTIVATION_SYSTEM,
    RETENTION_SYSTEM,
    UPSELL_SYSTEM,
    build_user_message,
)
from fintech_ai_segmentation.agent.schemas import RecommendationOutput
from fintech_ai_segmentation.app.repositories.customer import CustomerRepository
from fintech_ai_segmentation.app.schemas.customer import ActivityTimelineEntry, CustomerProfile


class AgentState(TypedDict):
    customer_id: uuid.UUID
    model_id: str
    profile: CustomerProfile | None
    timeline: list[ActivityTimelineEntry]
    strategy: str | None
    llm_response: str | None
    recommendation: RecommendationOutput | None


def _route(state: AgentState) -> str:
    cluster = (state["profile"].cluster_name if state["profile"] else None)
    if cluster == "at_risk_churner":
        return "generate_retention"
    if cluster == "high_value_active":
        return "generate_upsell"
    if cluster == "low_value_dormant":
        return "generate_reactivation"
    return "generate_activation"


def _strategy_node(system_prompt: str, strategy_name: str, llm_client: OpenRouterLLMClient):
    def node(state: AgentState) -> dict:
        profile = state["profile"]
        timeline = state["timeline"]
        cluster_avg_rfm = (
            profile.cluster_averages.rfm_score
            if profile and profile.cluster_averages
            else None
        )
        user_message = build_user_message(profile, timeline, cluster_avg_rfm, cohort_health=None)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        response = llm_client.complete(state["model_id"], messages)
        return {"strategy": strategy_name, "llm_response": response}
    return node


def _extract_json(text: str) -> str:
    """Strip markdown code fences if present, then return the JSON substring."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.rsplit("```", 1)[0]
    return text.strip()


def _validate_output(state: AgentState) -> dict:
    raw = _extract_json(state["llm_response"] or "")
    data = json.loads(raw)
    recommendation = RecommendationOutput(**data, strategy_used=state["strategy"])
    return {"recommendation": recommendation}


class LangGraphRecommendationAgent:
    def __init__(self, llm_client: OpenRouterLLMClient, repository: CustomerRepository) -> None:
        self._llm_client = llm_client
        self._repository = repository
        self._graph = self._build_graph()

    def _build_graph(self) -> object:
        g = StateGraph(AgentState)

        async def build_context(state: AgentState) -> dict:
            profile = await self._repository.get_customer_profile(state["customer_id"])
            timeline = await self._repository.get_activity_timeline(state["customer_id"])
            return {"profile": profile, "timeline": timeline or []}

        g.add_node("build_context", build_context)
        g.add_node("generate_retention", _strategy_node(RETENTION_SYSTEM, "retention", self._llm_client))
        g.add_node("generate_upsell", _strategy_node(UPSELL_SYSTEM, "upsell", self._llm_client))
        g.add_node("generate_reactivation", _strategy_node(REACTIVATION_SYSTEM, "reactivation", self._llm_client))
        g.add_node("generate_activation", _strategy_node(ACTIVATION_SYSTEM, "activation", self._llm_client))
        g.add_node("validate_output", _validate_output)

        g.set_entry_point("build_context")
        g.add_conditional_edges("build_context", _route, {
            "generate_retention": "generate_retention",
            "generate_upsell": "generate_upsell",
            "generate_reactivation": "generate_reactivation",
            "generate_activation": "generate_activation",
        })
        for node in ("generate_retention", "generate_upsell", "generate_reactivation", "generate_activation"):
            g.add_edge(node, "validate_output")
        g.add_edge("validate_output", END)

        return g.compile()

    async def run(self, customer_id: uuid.UUID, model_id: str = "smart-auto") -> RecommendationOutput:
        initial: AgentState = {
            "customer_id": customer_id,
            "model_id": model_id,
            "profile": None,
            "timeline": [],
            "strategy": None,
            "llm_response": None,
            "recommendation": None,
        }
        result = await self._graph.ainvoke(initial)
        return result["recommendation"]
