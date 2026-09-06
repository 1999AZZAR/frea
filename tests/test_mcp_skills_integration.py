from pathlib import Path
import sys
from unittest.mock import MagicMock
from src.agent import AgentLoop, ModelResponse, ToolCall
from src.executor import ToolExecutor, ToolRegistry
from src.mcp import MCPClient, MCPServerConfig
from tests.test_mcp import create_mock_mcp_server


def test_registry_includes_skill_tool(tmp_path: Path):
    skill_dir = tmp_path / "analyzer"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: analyzer\ndescription: Code analysis\n---\nRun analysis steps.",
        encoding="utf-8",
    )

    registry = ToolRegistry.with_defaults(include_skills=True, search_paths=[tmp_path])
    assert registry.get("skill") is not None

    executor = ToolExecutor(registry=registry, auto_approve=True)
    res = executor.execute("skill", {"name": "analyzer"})
    assert res.success is True
    assert '<skill_content name="analyzer">' in res.output
    assert "Run analysis steps." in res.output


def test_registry_mcp_tool_registration(tmp_path: Path):
    server_script = tmp_path / "mock_mcp.py"
    create_mock_mcp_server(server_script)

    config = MCPServerConfig(
        name="testserver",
        command=sys.executable,
        args=[str(server_script)],
    )
    client = MCPClient(config)
    assert client.start() is True

    try:
        registry = ToolRegistry.with_defaults(include_skills=False, include_mcp=False)
        registry.register_mcp_client(client)

        # Expected tool name: testserver_echo_test
        mcp_tool_name = "testserver_echo_test"
        defn = registry.get(mcp_tool_name)
        assert defn is not None
        assert "Echoes back" in defn.description

        # Execute via executor
        executor = ToolExecutor(registry=registry, auto_approve=True)
        res = executor.execute(mcp_tool_name, {"message": "OpenCode MCP Parity"})
        assert res.success is True
        assert res.output == "Echo: OpenCode MCP Parity"
    finally:
        client.stop()


def test_agent_loop_with_mcp_and_skills(tmp_path: Path):
    # Setup test skill
    skill_dir = tmp_path / "tester"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: tester\ndescription: Test skill\n---\nDo test.",
        encoding="utf-8",
    )

    # Setup MCP server
    server_script = tmp_path / "mock_mcp.py"
    create_mock_mcp_server(server_script)
    client = MCPClient(
        MCPServerConfig(name="srv", command=sys.executable, args=[str(server_script)])
    )
    assert client.start() is True

    try:
        registry = ToolRegistry.with_defaults(
            include_skills=True, search_paths=[tmp_path]
        )
        registry.register_mcp_client(client)

        executor = ToolExecutor(registry=registry, auto_approve=True)
        mock_provider = MagicMock()
        mock_provider.generate.side_effect = [
            # Call skill tool first
            ModelResponse(
                content="Loading skill...",
                tool_calls=[
                    ToolCall(id="c1", name="skill", arguments={"name": "tester"})
                ],
            ),
            # Call MCP tool second
            ModelResponse(
                content="Calling MCP...",
                tool_calls=[
                    ToolCall(
                        id="c2", name="srv_echo_test", arguments={"message": "hello"}
                    )
                ],
            ),
            # Final answer
            ModelResponse(content="All done.", tool_calls=[]),
        ]

        loop = AgentLoop(provider=mock_provider, executor=executor)
        result = loop.run("Run workflow")
        assert result.success is True
        assert result.final_answer == "All done."
        assert result.tool_calls_count == 2
    finally:
        client.stop()
