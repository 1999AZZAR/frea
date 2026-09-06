import sys
from unittest.mock import MagicMock, patch
from src.agent import BaseModelProvider
from src.providers import (
    GroqProvider,
    OpenAIProvider,
    compact_history,
    get_provider,
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
