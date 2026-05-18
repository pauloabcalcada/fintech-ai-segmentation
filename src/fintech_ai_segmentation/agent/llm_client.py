from __future__ import annotations

from openai import OpenAI
from langsmith import traceable

from fintech_ai_segmentation.app.settings import get_settings

_MODEL_MAP = {
    "gemini-flash-free": "google/gemma-4-31b-it:free",
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
            raise ValueError(f"Unknown model_id '{model_id}'. Valid options: {list(_MODEL_MAP)}")
        model = _MODEL_MAP[model_id]
        response = self._openai.chat.completions.create(model=model, messages=messages)
        return response.choices[0].message.content
