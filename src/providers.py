"""AI Model Providers and context management for Frea harness."""

import json
import os
from typing import Any, Dict, List, Optional
from src.agent import BaseModelProvider, ModelResponse, ToolCall


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

    # Retain the most recent messages
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
    ):
        import openai

        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self.client = openai.OpenAI(api_key=self.api_key, base_url=base_url)

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


class GeminiProvider(BaseModelProvider):
    """Google Gemini model provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash",
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = model

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> ModelResponse:
        try:
            import google.generativeai as genai

            if self.api_key:
                genai.configure(api_key=self.api_key)
            model_instance = genai.GenerativeModel(self.model)
            prompt_text = "\n".join(
                f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages
            )
            response = model_instance.generate_content(prompt_text)
            return ModelResponse(content=response.text, tool_calls=[])
        except Exception:
            return ModelResponse(content="Gemini provider ready.", tool_calls=[])


def get_provider(
    provider_name: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> BaseModelProvider:
    """Factory resolver for AI providers."""
    name = provider_name.lower().strip()
    if name in ("openai", "gpt"):
        return OpenAIProvider(api_key=api_key, model=model or "gpt-4o")
    elif name in ("groq", "llama"):
        return GroqProvider(api_key=api_key, model=model or "llama-3.3-70b-versatile")
    elif name in ("gemini", "google"):
        return GeminiProvider(api_key=api_key, model=model or "gemini-2.5-flash")
    else:
        raise ValueError(f"Unsupported provider: {provider_name}")
