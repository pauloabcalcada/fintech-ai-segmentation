from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from fintech_ai_segmentation.agent.llm_client import OpenRouterLLMClient

MESSAGES = [{"role": "user", "content": "hello"}]


def _make_client() -> tuple[OpenRouterLLMClient, MagicMock]:
    """Return a client and the mock chat.completions.create callable."""
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = "reply"

    mock_create = MagicMock(return_value=mock_completion)
    mock_openai = MagicMock()
    mock_openai.chat.completions.create = mock_create

    with patch("fintech_ai_segmentation.agent.llm_client.OpenAI", return_value=mock_openai):
        client = OpenRouterLLMClient(api_key="test-key")

    client._openai = mock_openai
    return client, mock_create


def test_gemini_flash_free_raises_value_error() -> None:
    client, _ = _make_client()
    with pytest.raises(ValueError, match="Unknown model_id"):
        client.complete("gemini-flash-free", MESSAGES)


def test_llama_70b_free_sends_correct_model_string() -> None:
    client, mock_create = _make_client()
    client.complete("llama-70b-free", MESSAGES)
    _, kwargs = mock_create.call_args
    assert kwargs["model"] == "meta-llama/llama-3.3-70b-instruct:free"


def test_mistral_7b_free_sends_correct_model_string() -> None:
    client, mock_create = _make_client()
    client.complete("mistral-7b-free", MESSAGES)
    _, kwargs = mock_create.call_args
    assert kwargs["model"] == "deepseek/deepseek-v4-flash:free"


def test_smart_auto_sends_openrouter_auto_model() -> None:
    client, mock_create = _make_client()
    client.complete("smart-auto", MESSAGES)
    _, kwargs = mock_create.call_args
    assert kwargs["model"] == "openrouter/auto"


def test_complete_returns_string_from_response() -> None:
    client, mock_create = _make_client()
    result = client.complete("gemini-2.5-flash-lite", MESSAGES)
    assert result == "reply"


def test_gemini_2_5_flash_lite_sends_correct_model_string() -> None:
    client, mock_create = _make_client()
    client.complete("gemini-2.5-flash-lite", MESSAGES)
    _, kwargs = mock_create.call_args
    assert kwargs["model"] == "google/gemini-2.5-flash-lite"


def test_none_choices_raises_value_error() -> None:
    mock_completion = MagicMock()
    mock_completion.choices = None

    mock_create = MagicMock(return_value=mock_completion)
    mock_openai = MagicMock()
    mock_openai.chat.completions.create = mock_create

    with patch("fintech_ai_segmentation.agent.llm_client.OpenAI", return_value=mock_openai):
        client = OpenRouterLLMClient(api_key="test-key")
    client._openai = mock_openai

    with pytest.raises(ValueError, match="no choices"):
        client.complete("llama-70b-free", MESSAGES)


def test_unknown_model_id_raises_value_error() -> None:
    client, _ = _make_client()
    with pytest.raises(ValueError, match="Unknown model_id"):
        client.complete("gpt-4o", MESSAGES)
