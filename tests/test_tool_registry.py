from unittest.mock import MagicMock
from src.agent import AgentLoop, ModelResponse, ToolCall
from src.executor import ToolDefinition, ToolExecutor, ToolRegistry
from src.tools import ToolResult


def test_tool_definition_openai_schema():
    defn = ToolDefinition(
        name="test_tool",
        description="A test tool",
        parameters={
            "type": "object",
            "properties": {"arg1": {"type": "string"}},
            "required": ["arg1"],
        },
        func=lambda arg1: ToolResult(success=True, output=arg1),
    )

    schema = defn.to_openai_schema()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "test_tool"
    assert schema["function"]["description"] == "A test tool"
    assert "arg1" in schema["function"]["parameters"]["properties"]


def test_tool_registry_with_defaults():
    registry = ToolRegistry.with_defaults()

    expected_tools = [
        "read_file",
        "write_file",
        "patch_file",
        "list_directory",
        "grep",
        "glob",
        "run_command",
        "command_status",
        "stop_command",
        "update_plan",
    ]
    for tool_name in expected_tools:
        defn = registry.get(tool_name)
        assert defn is not None, f"Missing tool: {tool_name}"
        assert defn.name == tool_name

    schemas = registry.to_openai_tools()
    assert len(schemas) >= len(expected_tools)
    names = [s["function"]["name"] for s in schemas]
    assert "read_file" in names
    assert "run_command" in names


def test_tool_executor_confirmation_guard():
    executor = ToolExecutor(auto_approve=False, confirm_fn=lambda name, args: False)
    # Destructive tool should be rejected
    res = executor.execute("write_file", {"path": "test.txt", "content": "hello"})
    assert res.success is False
    assert "rejected" in res.error.lower()

    # Read-only tool should execute without confirmation
    res_read = executor.execute("list_directory", {"path": "."})
    assert res_read.success is True


def test_tool_executor_auto_approve():
    confirm_mock = MagicMock(return_value=False)
    executor = ToolExecutor(auto_approve=True, confirm_fn=confirm_mock)

    res = executor.execute("run_command", {"command": "echo 'safe'"})
    assert res.success is True
    assert "safe" in res.output
    # confirm_mock should not even be called when auto_approve=True
    confirm_mock.assert_not_called()


def test_agent_loop_passes_tools_to_provider():
    mock_provider = MagicMock()
    executor = ToolExecutor(auto_approve=True)
    loop = AgentLoop(provider=mock_provider, executor=executor)

    # First turn calls a tool, second turn provides answer
    mock_provider.generate.side_effect = [
        ModelResponse(
            content="Checking files...",
            tool_calls=[
                ToolCall(
                    id="call_1", name="run_command", arguments={"command": "echo 'ok'"}
                )
            ],
        ),
        ModelResponse(content="Done checking.", tool_calls=[]),
    ]

    result = loop.run("Check files")
    assert result.success is True
    assert result.final_answer == "Done checking."
    assert result.tool_calls_count == 1
    assert mock_provider.generate.call_count == 2

    # Verify tools schema was provided to generate()
    first_call_kwargs = mock_provider.generate.call_args_list[0].kwargs
    assert "tools" in first_call_kwargs
    assert len(first_call_kwargs["tools"]) > 0
