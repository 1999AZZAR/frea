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

from src.agent import ModelResponse
from src.providers import (
    GeminiProvider,
    KiloCodeProvider,
    OpenAIProvider,
    OpenRouterProvider,
    OpencodeProvider,
    get_provider,
)


def test_opencode_provider_defaults():
    provider = OpencodeProvider()
    assert isinstance(provider, OpenAIProvider)
    # Confirmed base URL from models.dev: opencode.ai/zen/v1
    assert "opencode.ai/zen/v1" in str(provider.client.base_url)
    assert provider.client.api_key == "public"
    # Default free model (cost.input=0 confirmed)
    assert provider.model == "deepseek-v4-flash"


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


def test_openrouter_falls_back_to_opencode():
    provider = OpenRouterProvider(
        api_key="test-key",
        model="openrouter/auto",
        fallback_model="openrouter/free",
    )

    with patch.object(
        OpenAIProvider, "generate", side_effect=RuntimeError("OpenRouter failed")
    ):
        with patch.object(
            OpencodeProvider,
            "generate",
            return_value=ModelResponse(content="opencode success", tool_calls=[]),
        ) as mock_opencode_gen:
            resp = provider.generate([{"role": "user", "content": "hi"}])
            assert resp.content == "opencode success"
            mock_opencode_gen.assert_called_once()


def test_keyless_agent_loop_execution(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("KILOCODE_API_KEY", raising=False)

    from src.agent import AgentLoop
    from src.executor import ToolExecutor

    with patch("src.providers.get_vault_secret", return_value=None):
        provider = get_provider("opencode")
        executor = ToolExecutor(auto_approve=True)
        agent = AgentLoop(provider=provider, executor=executor)

        with patch.object(
            OpencodeProvider,
            "generate",
            return_value=ModelResponse(
                content="I am Frea, ready to assist.", tool_calls=[]
            ),
        ):
            result = agent.run("hello")
            assert result.success is True
            assert "ready to assist" in result.final_answer
