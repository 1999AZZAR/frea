from src.agent import (
    AgentLoop,
    AgentRunResult,
    BaseModelProvider,
    ModelResponse,
    ToolCall,
)
from src.executor import ToolExecutor


class MockProvider(BaseModelProvider):
    def __init__(self, responses):
        self.responses = list(responses)
        self.call_count = 0

    def generate(self, messages, tools=None):
        resp = self.responses[self.call_count]
        self.call_count += 1
        return resp


def test_agent_loop_direct_answer():
    """Agent returns immediate answer when no tool calls are produced."""
    provider = MockProvider(
        [
            ModelResponse(content="Hello, I am Frea.", tool_calls=[]),
        ]
    )
    executor = ToolExecutor(auto_approve=True)
    agent = AgentLoop(provider=provider, executor=executor)

    result = agent.run("hi")
    assert isinstance(result, AgentRunResult)
    assert result.success is True
    assert result.final_answer == "Hello, I am Frea."
    assert result.steps_taken == 1
    assert result.tool_calls_count == 0


def test_agent_loop_tool_execution_cycle():
    """Agent calls a tool, receives the output, and produces final answer."""
    provider = MockProvider(
        [
            ModelResponse(
                content="Let me find the python files.",
                tool_calls=[
                    ToolCall(
                        id="call_1",
                        name="find_files",
                        arguments={"pattern": "*.py", "path": "."},
                    ),
                ],
            ),
            ModelResponse(
                content="Found python files in the project.",
                tool_calls=[],
            ),
        ]
    )
    executor = ToolExecutor(auto_approve=True)
    agent = AgentLoop(provider=provider, executor=executor)

    result = agent.run("list py files")
    assert result.success is True
    assert result.final_answer == "Found python files in the project."
    assert result.steps_taken == 2
    assert result.tool_calls_count == 1


def test_agent_loop_max_steps():
    """Agent halts when max_steps limit is exceeded."""
    looping_call = ModelResponse(
        content="Looping...",
        tool_calls=[
            ToolCall(id="call_loop", name="find_files", arguments={"pattern": "*.txt"})
        ],
    )
    provider = MockProvider([looping_call] * 5)
    executor = ToolExecutor(auto_approve=True)
    agent = AgentLoop(provider=provider, executor=executor, max_steps=2)

    result = agent.run("infinite loop test")
    assert result.success is False
    assert "maximum steps" in result.final_answer.lower()
    assert result.steps_taken == 2
