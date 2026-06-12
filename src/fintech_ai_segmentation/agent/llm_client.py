"""OpenRouter LLM client wrapping the OpenAI SDK.

OpenRouter is API-compatible with OpenAI, so the standard ``openai.OpenAI``
client works by pointing ``base_url`` at OpenRouter's endpoint. This lets us
route to multiple model providers (Google, Meta, DeepSeek, OpenRouter auto)
through a single client without changing call sites.

``_MODEL_MAP`` translates short friendly aliases used in the rest of the
codebase into the full OpenRouter model path strings. Keeping this mapping
centralised means swapping the underlying model requires one line change here.

Every ``complete()`` call is wrapped with ``@traceable`` from LangSmith, which
records the full input/output, latency, and token counts in the LangSmith
dashboard for observability.
"""

from __future__ import annotations

from openai import OpenAI
from langsmith import traceable

from fintech_ai_segmentation.app.settings import get_settings

_MODEL_MAP = {
    "gemini-2.5-flash-lite": "google/gemini-2.5-flash-lite",
    "llama-70b-free": "meta-llama/llama-3.3-70b-instruct:free",
    "mistral-7b-free": "deepseek/deepseek-v4-flash:free",
    "smart-auto": "openrouter/auto",
}

_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterLLMClient:
    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or get_settings().OPENROUTER_API_KEY
        self._openai = OpenAI(
            api_key=key,
            base_url=_BASE_URL,
            timeout=60.0,
            default_headers={
                "HTTP-Referer": "https://github.com/pauloabcalcada/fintech-ai-segmentation",
                "X-Title": "Fintech AI Segmentation",
            },
        )

    @traceable(run_type="llm", name="openrouter_chat")
    def complete(self, model_id: str, messages: list[dict]) -> str:
        if model_id not in _MODEL_MAP:
            raise ValueError(
                f"Unknown model_id '{model_id}'. Valid options: {list(_MODEL_MAP)}"
            )
        model = _MODEL_MAP[model_id]
        response = self._openai.chat.completions.create(model=model, messages=messages)
        return response.choices[0].message.content
