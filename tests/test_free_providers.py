import sys
from unittest.mock import MagicMock, patch

try:
    import openai  # noqa: F401
except ImportError:
    mock_openai = MagicMock()

    class MockOpenAIClient:
        def __init__(self, api_key=None, base_url=None, default_headers=None, **kwargs):
            self.api_key = api_key
            self.base_url = base_url
            self.default_headers = default_headers or {}
            self.chat = MagicMock()

    mock_openai.OpenAI = MockOpenAIClient
    sys.modules["openai"] = mock_openai

from src.providers import (
    GeminiProvider,
    KiloCodeProvider,
    OpenAIProvider,
    OpencodeProvider,
    get_provider,
)


def test_opencode_provider_defaults():
    provider = OpencodeProvider()
    assert isinstance(provider, OpenAIProvider)
    assert "api.opencode.ai" in str(provider.client.base_url)
    assert provider.client.api_key == "public"
    assert "free" in provider.model.lower() or "kimi" in provider.model.lower()


def test_kilocode_provider_defaults():
    provider = KiloCodeProvider()
    assert isinstance(provider, OpenAIProvider)
    assert "api.kilo.ai" in str(provider.client.base_url)
    assert provider.client.api_key in ("public", "")
    assert "kilo" in provider.model.lower() or "free" in provider.model.lower()


def test_gemini_provider_openai_compatible():
    provider = GeminiProvider(api_key="test_gemini_key", model="gemini-2.5-flash")
    assert isinstance(provider, OpenAIProvider)
    assert "generativelanguage.googleapis.com" in str(provider.client.base_url)
    assert provider.client.api_key == "test_gemini_key"
    assert provider.model == "gemini-2.5-flash"


def test_get_provider_resolution():
    opencode = get_provider("opencode")
    assert isinstance(opencode, OpencodeProvider)

    kilo = get_provider("kilo")
    assert isinstance(kilo, KiloCodeProvider)

    kilocode = get_provider("kilocode")
    assert isinstance(kilocode, KiloCodeProvider)

    gemini = get_provider("gemini")
    assert isinstance(gemini, GeminiProvider)


def test_get_provider_keyless_fallback(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("KILOCODE_API_KEY", raising=False)

    with patch("src.providers.get_vault_secret", return_value=None):
        # Even with zero keys, default provider resolves cleanly and can instantiate
        provider = get_provider("opencode")
        assert provider.client.api_key == "public"
