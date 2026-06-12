"""LangGraph recommendation agent for SynaptiqPay customers.

The agent is a compiled StateGraph with five nodes:

  build_context → [conditional route] → generate_<strategy> → validate_output → END

Routing is based on the customer's cluster_name:
  - at_risk_churner   → retention
  - high_value_active → upsell
  - low_value_dormant → reactivation
  - anything else     → activation (no transaction history / new customer)

``_strategy_node`` is a factory that creates an async LangGraph node for a
given strategy. It builds the prompt, calls the LLM via ``OpenRouterLLMClient``,
and stores the raw string response in state for ``_validate_output`` to parse.

``_validate_output`` handles malformed LLM responses: strips markdown fences,
attempts to close truncated JSON, then validates with Pydantic. Missing optional
fields are filled with safe defaults rather than raising, so a partial LLM
response never crashes the API.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import TypedDict

from langgraph.graph import END, StateGraph

from fintech_ai_segmentation.agent.llm_client import OpenRouterLLMClient
from fintech_ai_segmentation.agent.prompts import (
    build_system_prompt,
    build_user_message,
)
from fintech_ai_segmentation.agent.schemas import RecommendationOutput
from fintech_ai_segmentation.app.repositories.customer import CustomerRepository
from fintech_ai_segmentation.app.schemas.customer import (
    ActivityTimelineEntry,
    CustomerProfile,
)


class AgentState(TypedDict):
    customer_id: uuid.UUID
    model_id: str
    language: str
    profile: CustomerProfile | None
    timeline: list[ActivityTimelineEntry]
    strategy: str | None
    llm_response: str | None
    recommendation: RecommendationOutput | None


def _route(state: AgentState) -> str:
    cluster = state["profile"].cluster_name if state["profile"] else None
    if cluster == "at_risk_churner":
        return "generate_retention"
    if cluster == "high_value_active":
        return "generate_upsell"
    if cluster == "low_value_dormant":
        return "generate_reactivation"
    return "generate_activation"


def _strategy_node(strategy_name: str, llm_client: OpenRouterLLMClient):
    async def node(state: AgentState) -> dict:
        profile = state["profile"]
        timeline = state["timeline"]
        cluster_avg_rfm = (
            profile.cluster_averages.rfm_score
            if profile and profile.cluster_averages
            else None
        )
        system_prompt = build_system_prompt(strategy_name, state["language"])
        user_message = build_user_message(
            profile, timeline, cluster_avg_rfm, cohort_health=None
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        response = await asyncio.to_thread(
            llm_client.complete, state["model_id"], messages
        )
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


def _repair_json(text: str) -> str:
    """Attempt to fix truncated JSON by closing unclosed strings/objects."""
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass
    for suffix in ("\n}", "}", '"}', '"}\n'):
        try:
            json.loads(text + suffix)
            return text + suffix
        except json.JSONDecodeError:
            pass
    return text


_VALID_RISK_LEVELS = {"low", "medium", "high", "critical"}


def _validate_output(state: AgentState) -> dict:
    raw = _repair_json(_extract_json(state["llm_response"] or ""))
    data = json.loads(raw)

    if data.get("risk_level") not in _VALID_RISK_LEVELS:
        data["risk_level"] = "medium"

    data.setdefault("suggested_product", "none")
    data.setdefault("message_tone", "professional")
    data.setdefault(
        "reasoning", data.get("recommended_action", "No reasoning provided.")
    )
    data.setdefault("notification_text", "")

    recommendation = RecommendationOutput(**data, strategy_used=state["strategy"])
    return {"recommendation": recommendation}


class LangGraphRecommendationAgent:
    def __init__(
        self, llm_client: OpenRouterLLMClient, repository: CustomerRepository
    ) -> None:
        self._llm_client = llm_client
        self._repository = repository
        self._graph = self._build_graph()

    def _build_graph(self) -> object:
        g = StateGraph(AgentState)

        async def build_context(state: AgentState) -> dict:
            profile = await self._repository.get_customer_profile(state["customer_id"])
            timeline = await self._repository.get_activity_timeline(
                state["customer_id"]
            )
            return {"profile": profile, "timeline": timeline or []}

        g.add_node("build_context", build_context)
        g.add_node("generate_retention", _strategy_node("retention", self._llm_client))
        g.add_node("generate_upsell", _strategy_node("upsell", self._llm_client))
        g.add_node(
            "generate_reactivation", _strategy_node("reactivation", self._llm_client)
        )
        g.add_node(
            "generate_activation", _strategy_node("activation", self._llm_client)
        )
        g.add_node("validate_output", _validate_output)

        g.set_entry_point("build_context")
        g.add_conditional_edges(
            "build_context",
            _route,
            {
                "generate_retention": "generate_retention",
                "generate_upsell": "generate_upsell",
                "generate_reactivation": "generate_reactivation",
                "generate_activation": "generate_activation",
            },
        )
        for node in (
            "generate_retention",
            "generate_upsell",
            "generate_reactivation",
            "generate_activation",
        ):
            g.add_edge(node, "validate_output")
        g.add_edge("validate_output", END)

        return g.compile()

    async def run(
        self, customer_id: uuid.UUID, model_id: str = "smart-auto", language: str = "en"
    ) -> RecommendationOutput:
        initial: AgentState = {
            "customer_id": customer_id,
            "model_id": model_id,
            "language": language,
            "profile": None,
            "timeline": [],
            "strategy": None,
            "llm_response": None,
            "recommendation": None,
        }
        result = await self._graph.ainvoke(initial)
        return result["recommendation"]
