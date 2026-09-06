from src.agent import AgentLoop, ModelResponse
from src.chat_config import ChatConfig
from src.executor import ToolExecutor


class DummyProvider:
    def __init__(self):
        self.last_messages = []

    def generate(self, messages, tools=None):
        self.last_messages = messages
        return ModelResponse(content="I am Frea, ready to assist.", tool_calls=[])


def test_agent_loop_default_prompt_contains_frea_persona():
    provider = DummyProvider()
    executor = ToolExecutor(auto_approve=True)
    agent = AgentLoop(provider=provider, executor=executor)

    assert "Frea" in agent.system_prompt
    assert "Azzar" in agent.system_prompt


def test_agent_loop_run_passes_persona_in_system_message():
    provider = DummyProvider()
    executor = ToolExecutor(auto_approve=True)
    agent = AgentLoop(provider=provider, executor=executor)

    result = agent.run("Who are you?")
    assert result.success is True
    assert len(provider.last_messages) >= 2
    assert provider.last_messages[0]["role"] == "system"
    assert "Frea" in provider.last_messages[0]["content"]
    assert "Azzar" in provider.last_messages[0]["content"]


def test_chat_config_instruction_fallback_loads_canonical_persona():
    # Calling chat_instruction on nonexistent file should fall back to load_frea_persona()
    instruction = ChatConfig.chat_instruction("/nonexistent/file.txt")
    assert "Frea" in instruction
    assert "Azzar" in instruction
