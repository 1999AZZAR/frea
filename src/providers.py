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


class FreaProviderError(Exception):
    """Raised when a provider call fails with a user-actionable message."""


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
        import openai

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        try:
            response = self.client.chat.completions.create(**kwargs)
        except openai.AuthenticationError as exc:
            body = getattr(exc, "body", {}) or {}
            err_dict = body.get("error", {}) if isinstance(body, dict) else {}
            code = err_dict.get("code", "") if isinstance(err_dict, dict) else ""
            msg = str(exc)
            if (
                code == "PAID_MODEL_AUTH_REQUIRED"
                or "Missing API key" in msg
                or "401" in msg
                or "AuthError" in msg
                or "sign in" in msg.lower()
            ):
                raise FreaProviderError(
                    f"Model '{self.model}' requires an API key.\n"
                    "Switch to a free model with /model:\n"
                    "  • kilo-auto/free              (KiloCode Gateway, free)\n"
                    "  • nemotron-3.5-lightning-free (OpenCode Zen, free)\n"
                    "  • mimo-v2.5-free              (OpenCode Zen, free)"
                ) from exc
            raise FreaProviderError(
                f"Authentication failed for '{self.model}': {exc}"
            ) from exc
        except openai.RateLimitError as exc:
            raise FreaProviderError(
                f"Rate limit hit for '{self.model}'. Try /model to switch providers."
            ) from exc
        except openai.APIConnectionError as exc:
            raise FreaProviderError(
                f"Cannot reach API for '{self.model}': {exc}"
            ) from exc

        choice = response.choices[0].message
        content = choice.content
        if not content:
            extra = getattr(choice, "model_extra", {}) or {}
            content = (
                extra.get("reasoning_content")
                or getattr(choice, "reasoning", None)
                or ""
            )

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

        return ModelResponse(content=content, tool_calls=tool_calls)


class OpenRouterProvider(OpenAIProvider):
    """OpenRouter provider — smart routing with automatic free fallback."""

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
                # Match opencode headers exactly (models.dev convention)
                "HTTP-Referer": "https://opencode.ai/",
                "X-Title": "opencode",
            },
        )

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> ModelResponse:
        try:
            return super().generate(messages, tools=tools)
        except FreaProviderError:
            raise
        except Exception:
            pass

        # Try openrouter/free tier
        if self.model != self.fallback_model:
            original_model = self.model
            self.model = self.fallback_model
            try:
                return super().generate(messages, tools=tools)
            except Exception:
                pass
            finally:
                self.model = original_model

        # Fall through to KiloCode free gateway
        try:
            return KiloCodeProvider().generate(messages, tools=tools)
        except Exception:
            pass

        # Last resort: OpenCode Zen free
        return OpencodeProvider().generate(messages, tools=tools)


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
    """OpenCode Zen gateway — free models (cost.input=0) work with apiKey='public'.

    Paid models require OPENCODE_API_KEY.
    Base URL confirmed from models.dev: https://opencode.ai/zen/v1
    """

    # Free models available without auth (cost.input == 0 on models.dev)
    FREE_MODELS = [
        "nemotron-3.5-lightning-free",
        "mimo-v2.5-free",
        "deepseek-v4-flash-free",
        "ring-2.6-1t-free",
    ]
    DEFAULT_FREE_MODEL = "nemotron-3.5-lightning-free"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        key = api_key or os.environ.get("OPENCODE_API_KEY") or "public"
        super().__init__(
            api_key=key,
            model=model or self.DEFAULT_FREE_MODEL,
            base_url="https://opencode.ai/zen/v1",
            default_headers={
                "User-Agent": "opencode/1.0.0",
                "HTTP-Referer": "https://opencode.ai/",
                "X-Title": "opencode",
            },
        )


class KiloCodeProvider(OpenAIProvider):
    """KiloCode gateway — free tier works with apiKey='public'.

    Base URL confirmed from kilo.ts plugin: https://api.kilo.ai/api/gateway
    Requires KILO_API_KEY for paid models.
    """

    DEFAULT_FREE_MODEL = "kilo-auto/free"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        key = api_key or os.environ.get("KILO_API_KEY") or "public"
        super().__init__(
            api_key=key,
            model=model or self.DEFAULT_FREE_MODEL,
            base_url="https://api.kilo.ai/api/gateway",
            default_headers={
                "User-Agent": "opencode/1.0.0",
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
    """
    Factory resolver for AI providers with free model support.

    Provider auto-detection precedence (from model string):
      openrouter/…  → OpenRouter
      kilocode/…    → KiloCode
      kilo/…        → KiloCode
      gemini-…      → Gemini
      gpt-…         → OpenAI
      llama-… / groq → Groq
      *-free / kimi / ring / mimo / deepseek-v4 → OpencodeProvider (Zen)
      anything else → OpenRouter (paid model, need OPENROUTER_API_KEY)
    """
    name = provider_name.lower().strip()
    effective_model = model or provider_name

    # Explicit provider name matches — use model param only (provider uses its own default if None)
    if name in ("opencode", "opencode-zen", "zen"):
        return OpencodeProvider(api_key=api_key, model=model)
    if name in ("kilo", "kilocode", "kilo-code"):
        return KiloCodeProvider(api_key=api_key, model=model)
    if "openrouter" in name or name == "default":
        return OpenRouterProvider(
            api_key=api_key,
            model=model or "openrouter/auto",
            fallback_model="openrouter/free",
        )
    if name in ("openai", "gpt"):
        return OpenAIProvider(api_key=api_key, model=model or "gpt-4o")
    if name in ("groq", "llama", "mixtral"):
        return GroqProvider(api_key=api_key, model=model or "llama-3.3-70b-versatile")
    if name in ("gemini", "google"):
        return GeminiProvider(api_key=api_key, model=model or "gemini-2.5-flash")

    # Model-string inference (when full model ID passed as provider_name)
    m = effective_model.lower()
    if m.startswith("openrouter/"):
        return OpenRouterProvider(api_key=api_key, model=effective_model)
    if m.startswith(("kilocode/", "kilo/", "kilo-", "kilocode-")):
        return KiloCodeProvider(api_key=api_key, model=effective_model)
    if m.startswith(("gemini-", "gemini/")):
        return GeminiProvider(api_key=api_key, model=effective_model)
    if m.startswith(("gpt-", "o1-", "o3-", "o4-")):
        return OpenAIProvider(api_key=api_key, model=effective_model)
    if m.startswith("llama-") or m.startswith("mixtral-") or "groq" in m:
        return GroqProvider(api_key=api_key, model=effective_model)
    if (
        m.endswith("-free")
        or ":free" in m
        or "kimi" in m
        or "mimo" in m
        or "nemotron" in m
        or m.startswith("ring-")
        or m.startswith("deepseek-v4")
        or m.startswith("minimax")
        or m.startswith("glm-")
    ):
        return OpencodeProvider(api_key=api_key, model=effective_model)

    # Unknown: route through OpenRouter (handles most model IDs)
    return OpenRouterProvider(
        api_key=api_key,
        model=effective_model,
        fallback_model="openrouter/free",
    )
