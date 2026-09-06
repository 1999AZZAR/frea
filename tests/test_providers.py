import sys
from unittest.mock import MagicMock, patch
from src.agent import BaseModelProvider, ModelResponse
from src.providers import (
    GroqProvider,
    OpenAIProvider,
    OpenRouterProvider,
    compact_history,
    get_provider,
    get_vault_secret,
)


def test_get_provider_openai():
    mock_openai = MagicMock()
    with patch.dict(sys.modules, {"openai": mock_openai}):
        provider = get_provider("openai", api_key="sk-test", model="gpt-4o")
        assert isinstance(provider, OpenAIProvider)
        assert isinstance(provider, BaseModelProvider)
        assert provider.model == "gpt-4o"


def test_get_provider_groq():
    mock_openai = MagicMock()
    with patch.dict(sys.modules, {"openai": mock_openai}):
        provider = get_provider(
            "groq", api_key="gsk-test", model="llama-3.3-70b-versatile"
        )
        assert isinstance(provider, GroqProvider)
        assert isinstance(provider, BaseModelProvider)


def test_get_provider_openrouter_default():
    mock_openai = MagicMock()
    with patch.dict(sys.modules, {"openai": mock_openai}):
        provider = get_provider("openrouter")
        assert isinstance(provider, OpenRouterProvider)
        assert isinstance(provider, BaseModelProvider)
        assert provider.model == "openrouter/auto"
        assert provider.fallback_model == "openrouter/free"


def test_openrouter_fallback_mechanism():
    mock_openai = MagicMock()
    with patch.dict(sys.modules, {"openai": mock_openai}):
        provider = OpenRouterProvider(
            api_key="test-key",
            model="openrouter/auto",
            fallback_model="openrouter/free",
        )

        call_models = []

        def mock_generate(messages, tools=None):
            call_models.append(provider.model)
            if provider.model == "openrouter/auto":
                raise RuntimeError("Rate limited on auto")
            return ModelResponse(content="fallback success", tool_calls=[])

        provider.client.chat.completions.create = MagicMock()
        # Patch generate on super or test fallback directly
        with patch.object(OpenAIProvider, "generate", side_effect=mock_generate):
            res = provider.generate([{"role": "user", "content": "hi"}])
            assert res.content == "fallback success"
            assert "openrouter/auto" in call_models
            assert "openrouter/free" in call_models


def test_get_vault_secret_live():
    # Verify vault retrieval for openrouter_01 works
    secret = get_vault_secret("openrouter_01")
    assert secret is not None
    assert secret.startswith("sk-or-v1-")


def test_compact_history_under_limit():
    messages = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]
    compacted = compact_history(messages, max_messages=10)
    assert len(compacted) == 3
    assert compacted == messages


def test_compact_history_over_limit():
    messages = [{"role": "system", "content": "sys"}]
    for i in range(30):
        messages.append({"role": "user", "content": f"msg {i}"})

    compacted = compact_history(messages, max_messages=10)
    assert len(compacted) <= 12
    assert compacted[0]["role"] == "system"
    assert compacted[-1]["content"] == "msg 29"
