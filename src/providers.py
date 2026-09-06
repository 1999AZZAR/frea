"""AI Model Providers and context management for Frea harness."""

import json
import os
import subprocess
from typing import Any, Dict, List, Optional
from src.agent import BaseModelProvider, ModelResponse, ToolCall


def get_vault_secret(service_name: str = "openrouter_01") -> Optional[str]:
    """Retrieve secret from local mema-vault securely."""
    vault_script = os.path.expanduser(
        "~/.gemini/config/skills/mema-vault/scripts/vault.py"
    )
    if not os.path.exists(vault_script):
        return None
    try:
        proc = subprocess.run(
            ["python3", vault_script, "get", service_name, "--show"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                if line.startswith("Pass: "):
                    return line[6:].strip()
    except Exception:
        pass
    return None


def compact_history(
    messages: List[Dict[str, Any]], max_messages: int = 20
) -> List[Dict[str, Any]]:
    """Prune conversation history to maintain token budget while keeping context."""
    if len(messages) <= max_messages:
        return list(messages)

    system_msg = (
        messages[0] if messages and messages[0].get("role") == "system" else None
    )
    remaining_budget = max_messages - (1 if system_msg else 0)

    recent_messages = messages[-remaining_budget:]
    compacted = [system_msg] if system_msg else []
    compacted.extend(recent_messages)
    return compacted


class OpenAIProvider(BaseModelProvider):
    """OpenAI API provider for tool calling and completions."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        base_url: Optional[str] = None,
        default_headers: Optional[Dict[str, str]] = None,
    ):
        import openai

        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        kwargs: Dict[str, Any] = {"api_key": self.api_key or "dummy"}
        if base_url:
            kwargs["base_url"] = base_url
        if default_headers:
            kwargs["default_headers"] = default_headers
        self.client = openai.OpenAI(**kwargs)

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> ModelResponse:
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        response = self.client.chat.completions.create(**kwargs)
        choice = response.choices[0].message

        tool_calls: List[ToolCall] = []
        if choice.tool_calls:
            for tc in choice.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                tool_calls.append(
                    ToolCall(id=tc.id, name=tc.function.name, arguments=args)
                )

        return ModelResponse(content=choice.content, tool_calls=tool_calls)


class OpenRouterProvider(OpenAIProvider):
    """OpenRouter provider supporting auto model routing and fallback."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "openrouter/auto",
        fallback_model: str = "openrouter/free",
    ):
        key = (
            api_key
            or os.environ.get("OPENROUTER_API_KEY")
            or get_vault_secret("openrouter_01")
            or ""
        )
        self.fallback_model = fallback_model
        super().__init__(
            api_key=key,
            model=model,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/1999AZZAR/frea",
                "X-Title": "Frea",
            },
        )

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> ModelResponse:
        try:
            return super().generate(messages, tools=tools)
        except Exception as exc:
            if self.fallback_model and self.model != self.fallback_model:
                original_model = self.model
                self.model = self.fallback_model
                try:
                    return super().generate(messages, tools=tools)
                except Exception:
                    self.model = original_model
            try:
                free_provider = OpencodeProvider()
                return free_provider.generate(messages, tools=tools)
            except Exception:
                pass
            raise exc


class GroqProvider(OpenAIProvider):
    """Groq API provider utilizing ultra-fast OpenAI-compatible endpoints."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile",
    ):
        groq_key = api_key or os.environ.get("GROQ_API_KEY", "")
        super().__init__(
            api_key=groq_key,
            model=model,
            base_url="https://api.groq.com/openai/v1",
        )


class OpencodeProvider(OpenAIProvider):
    """OpenCode gateway provider with free out-of-the-box models."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "kimi-k2.5-free",
    ):
        key = api_key or os.environ.get("OPENCODE_API_KEY") or "public"
        super().__init__(
            api_key=key,
            model=model,
            base_url="https://api.opencode.ai/v1",
            default_headers={
                "HTTP-Referer": "https://opencode.ai/",
                "X-Title": "opencode",
            },
        )


class KiloCodeProvider(OpenAIProvider):
    """KiloCode gateway provider supporting smart free routing."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "kilocode/kilo-auto/balanced",
    ):
        key = api_key or os.environ.get("KILOCODE_API_KEY") or "public"
        super().__init__(
            api_key=key,
            model=model,
            base_url="https://api.kilo.ai/api/gateway",
            default_headers={
                "HTTP-Referer": "https://opencode.ai/",
                "X-Title": "opencode",
            },
        )


class GeminiProvider(OpenAIProvider):
    """Google Gemini model provider using standard OpenAI-compatible endpoint."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash",
    ):
        key = api_key or os.environ.get("GEMINI_API_KEY", "")
        super().__init__(
            api_key=key,
            model=model,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )


def get_provider(
    provider_name: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> BaseModelProvider:
    """Factory resolver for AI providers with free model support."""
    name = provider_name.lower().strip()
    if name in ("opencode", "opencode/free"):
        return OpencodeProvider(api_key=api_key, model=model or "kimi-k2.5-free")
    elif name in ("kilo", "kilocode"):
        return KiloCodeProvider(
            api_key=api_key, model=model or "kilocode/kilo-auto/balanced"
        )
    elif "openrouter" in name or name == "default":
        return OpenRouterProvider(
            api_key=api_key,
            model=model or "openrouter/auto",
            fallback_model="openrouter/free",
        )
    elif name in ("openai", "gpt"):
        return OpenAIProvider(api_key=api_key, model=model or "gpt-4o")
    elif name in ("groq", "llama"):
        return GroqProvider(api_key=api_key, model=model or "llama-3.3-70b-versatile")
    elif name in ("gemini", "google"):
        return GeminiProvider(api_key=api_key, model=model or "gemini-2.5-flash")
    elif "kimi" in name or "free" in name:
        return OpencodeProvider(api_key=api_key, model=model or provider_name)
    else:
        return OpenRouterProvider(
            api_key=api_key,
            model=model or provider_name,
            fallback_model="openrouter/free",
        )
