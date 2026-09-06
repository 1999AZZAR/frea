from pathlib import Path
import sys
from src.mcp import MCPClient, MCPServerConfig, load_mcp_servers


def create_mock_mcp_server(script_path: Path):
    """Write a minimal stdio MCP server in Python for testing."""
    code = """
import sys
import json

def handle():
    for line in sys.stdin:
        if not line.strip():
            continue
        req = json.loads(line)
        method = req.get("method")
        msg_id = req.get("id")

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "test-mock-server", "version": "1.0.0"}
                }
            }
            sys.stdout.write(json.dumps(resp) + "\\n")
            sys.stdout.flush()
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": "echo_test",
                            "description": "Echoes back provided input",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"message": {"type": "string"}},
                                "required": ["message"]
                            }
                        }
                    ]
                }
            }
            sys.stdout.write(json.dumps(resp) + "\\n")
            sys.stdout.flush()
        elif method == "tools/call":
            params = req.get("params", {})
            tool_name = params.get("name")
            args = params.get("arguments", {})
            if tool_name == "echo_test":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Echo: {args.get('message')}"}],
                        "isError": False
                    }
                }
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": "Method not found"}
                }
            sys.stdout.write(json.dumps(resp) + "\\n")
            sys.stdout.flush()

if __name__ == "__main__":
    handle()
"""
    script_path.write_text(code, encoding="utf-8")


def test_mcp_client_handshake_and_tool_call(tmp_path: Path):
    server_script = tmp_path / "mock_mcp.py"
    create_mock_mcp_server(server_script)

    config = MCPServerConfig(
        name="mock",
        command=sys.executable,
        args=[str(server_script)],
    )

    client = MCPClient(config)
    try:
        assert client.start() is True
        tools = client.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "echo_test"
        assert "Echoes back" in tools[0]["description"]

        # Call tool
        res = client.call_tool("echo_test", {"message": "Antigravity"})
        assert res.success is True
        assert res.output == "Echo: Antigravity"
    finally:
        client.stop()


def test_load_mcp_servers_from_dict(tmp_path: Path):
    server_script = tmp_path / "mock_mcp.py"
    create_mock_mcp_server(server_script)

    config_data = {
        "mcpServers": {
            "demo": {
                "command": sys.executable,
                "args": [str(server_script)],
            }
        }
    }

    clients = load_mcp_servers(config_data)
    try:
        assert "demo" in clients
        demo_client = clients["demo"]
        tools = demo_client.list_tools()
        assert len(tools) == 1
    finally:
        for c in clients.values():
            c.stop()
