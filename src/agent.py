"""Agentic ReAct reasoning and execution loop for Frea."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import json
from typing import Any, Callable, Dict, List, Optional
from src.executor import ToolExecutor


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ModelResponse:
    content: Optional[str] = None
    tool_calls: List[ToolCall] = field(default_factory=list)


class BaseModelProvider(ABC):
    """Abstract interface for AI LLM providers."""

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> ModelResponse:
        """Generate response given chat messages and tool declarations."""
        pass


@dataclass
class AgentRunResult:
    final_answer: str
    steps_taken: int
    tool_calls_count: int
    success: bool


try:
    from src.persona import load_frea_persona
except ImportError:
    from persona import load_frea_persona


def get_default_system_prompt() -> str:
    """Return canonical Frea persona as system prompt."""
    return load_frea_persona()


class AgentLoop:
    """Multi-turn ReAct reasoning and tool dispatch engine."""

    def __init__(
        self,
        provider: BaseModelProvider,
        executor: ToolExecutor,
        max_steps: int = 15,
        system_prompt: Optional[str] = None,
        on_tool_call: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        on_tool_result: Optional[Callable[[str, Dict[str, Any], str], None]] = None,
    ):
        self.provider = provider
        self.executor = executor
        self.max_steps = max_steps
        self.on_tool_call = on_tool_call
        self.on_tool_result = on_tool_result
        base_prompt = system_prompt or get_default_system_prompt()
        try:
            from src.skills import discover_skills, render_skills_prompt

            skills = discover_skills()
            skills_prompt = render_skills_prompt(skills)
            if skills_prompt and "<skills>" not in base_prompt:
                base_prompt = f"{base_prompt}\n\n{skills_prompt}"
        except Exception:
            pass
        self.system_prompt = base_prompt

    def run(self, user_prompt: str) -> AgentRunResult:
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        steps_taken = 0
        tool_calls_count = 0

        while steps_taken < self.max_steps:
            steps_taken += 1
            tools = (
                self.executor.get_tool_schemas()
                if hasattr(self.executor, "get_tool_schemas")
                else None
            )
            try:
                response = self.provider.generate(messages, tools=tools)
            except Exception as exc:
                # Surface provider errors (auth, rate-limit, etc.) as a final answer
                from src.providers import FreaProviderError

                err_msg = (
                    str(exc)
                    if isinstance(exc, FreaProviderError)
                    else f"Provider error: {exc}"
                )
                return AgentRunResult(
                    final_answer=err_msg,
                    steps_taken=steps_taken,
                    tool_calls_count=tool_calls_count,
                    success=False,
                )

            # If no tools called, we have our final answer
            if not response.tool_calls:
                final_text = response.content or ""
                return AgentRunResult(
                    final_answer=final_text,
                    steps_taken=steps_taken,
                    tool_calls_count=tool_calls_count,
                    success=True,
                )

            # Record assistant turn with tool calls
            messages.append(
                {
                    "role": "assistant",
                    "content": response.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            },
                        }
                        for tc in response.tool_calls
                    ],
                }
            )

            # Execute each requested tool call
            for tc in response.tool_calls:
                tool_calls_count += 1
                if self.on_tool_call:
                    try:
                        self.on_tool_call(tc.name, tc.arguments)
                    except Exception:
                        pass

                result = self.executor.execute(tc.name, tc.arguments)
                tool_output = (
                    result.output if result.success else f"Error: {result.error}"
                )

                if self.on_tool_result:
                    try:
                        self.on_tool_result(tc.name, tc.arguments, tool_output)
                    except Exception:
                        pass

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.name,
                        "content": tool_output,
                    }
                )

        return AgentRunResult(
            final_answer="Halted: Reached maximum steps without completion.",
            steps_taken=steps_taken,
            tool_calls_count=tool_calls_count,
            success=False,
        )
