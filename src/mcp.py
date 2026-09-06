"""Model Context Protocol (MCP) stdio client and server manager (OpenCode parity)."""

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import subprocess
import threading
from typing import Any, Dict, List, Optional
from src.tools import ToolResult


@dataclass
class MCPServerConfig:
    """Configuration definition for an individual stdio MCP server."""

    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Optional[Dict[str, str]] = None


class MCPClient:
    """Stdio transport client communicating via JSON-RPC 2.0 with an MCP server."""

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self._msg_id = 0
        self._lock = threading.Lock()

    def _next_id(self) -> int:
        self._msg_id += 1
        return self._msg_id

    def start(self) -> bool:
        """Launch MCP server subprocess and execute protocol handshake."""
        try:
            env = os.environ.copy()
            if self.config.env:
                env.update(self.config.env)

            cmd = [self.config.command] + self.config.args
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=env,
            )

            # Send initialize handshake
            req_id = self._next_id()
            init_req = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "frea", "version": "1.0.0"},
                },
            }
            resp = self._send_request(init_req)
            if not resp or "result" not in resp:
                self.stop()
                return False

            # Send initialized notification
            notif = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            }
            self._send_notification(notif)
            return True
        except Exception:
            self.stop()
            return False

    def is_connected(self) -> bool:
        """Check if MCP server subprocess is active and alive."""
        return bool(self.process and self.process.poll() is None)

    def _send_request(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            if not self.process or not self.process.stdin or not self.process.stdout:
                return None
            try:
                line = json.dumps(payload) + "\n"
                self.process.stdin.write(line)
                self.process.stdin.flush()

                resp_line = self.process.stdout.readline()
                if not resp_line:
                    return None
                return json.loads(resp_line)
            except Exception:
                return None

    def _send_notification(self, payload: Dict[str, Any]) -> None:
        with self._lock:
            if not self.process or not self.process.stdin:
                return
            try:
                line = json.dumps(payload) + "\n"
                self.process.stdin.write(line)
                self.process.stdin.flush()
            except Exception:
                pass

    def list_tools(self) -> List[Dict[str, Any]]:
        """Query server for available tools."""
        req_id = self._next_id()
        req = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": "tools/list",
            "params": {},
        }
        resp = self._send_request(req)
        if not resp or "result" not in resp:
            return []
        return resp["result"].get("tools", [])

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Invoke an MCP tool with provided parameters."""
        req_id = self._next_id()
        req = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments,
            },
        }
        resp = self._send_request(req)
        if not resp:
            return ToolResult(
                success=False, error=f"No response from MCP server '{self.config.name}'"
            )

        if "error" in resp:
            err = resp["error"]
            msg = err.get("message", "Unknown error")
            return ToolResult(
                success=False,
                error=f"MCP error ({err.get('code', -1)}): {msg}",
            )

        result = resp.get("result", {})
        is_error = result.get("isError", False)
        content_items = result.get("content", [])

        texts = []
        for item in content_items:
            if isinstance(item, dict) and item.get("type") == "text":
                texts.append(item.get("text", ""))

        output_str = "\n".join(texts)
        if is_error:
            return ToolResult(
                success=False,
                error=output_str or "MCP tool returned an error",
            )
        return ToolResult(success=True, output=output_str)

    def stop(self) -> None:
        """Safely terminate MCP server subprocess."""
        with self._lock:
            if self.process:
                try:
                    if self.process.stdin:
                        self.process.stdin.close()
                    self.process.terminate()
                    self.process.wait(timeout=1)
                except Exception:
                    try:
                        self.process.kill()
                    except Exception:
                        pass
                self.process = None


def load_mcp_servers(config: Dict[str, Any]) -> Dict[str, MCPClient]:
    """Parse configuration and spin up active MCP clients."""
    servers_dict = (
        config.get("mcp") or config.get("mcpServers") or config.get("mcp_servers") or {}
    )
    active_clients: Dict[str, MCPClient] = {}

    for server_name, spec in servers_dict.items():
        if not isinstance(spec, dict):
            continue

        # Respect enabled flag (default: True)
        if spec.get("enabled") is False:
            continue

        # Stdio / local subprocess servers only
        server_type = spec.get("type", "local")
        if server_type not in ("local", "stdio"):
            continue

        raw_cmd = spec.get("command")
        if not raw_cmd:
            continue

        if isinstance(raw_cmd, list):
            if not raw_cmd:
                continue
            command = raw_cmd[0]
            args = raw_cmd[1:] + spec.get("args", [])
        else:
            command = raw_cmd
            args = spec.get("args", [])

        env = spec.get("environment") or spec.get("env")

        cfg = MCPServerConfig(
            name=server_name,
            command=command,
            args=args,
            env=env,
        )
        client = MCPClient(cfg)
        if client.start():
            active_clients[server_name] = client

    return active_clients


def load_user_mcp_servers() -> Dict[str, MCPClient]:
    """Scan ~/.config/frea/config.json, ~/.config/frea/mcp.json, and fallback to ~/.config/opencode/opencode.json."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    config_dir = Path(xdg) / "frea" if xdg else Path.home() / ".config" / "frea"

    mcp_config = {}
    config_file = config_dir / "config.json"
    if config_file.exists():
        try:
            mcp_config.update(json.loads(config_file.read_text(encoding="utf-8")))
        except Exception:
            pass

    mcp_file = config_dir / "mcp.json"
    if mcp_file.exists():
        try:
            mcp_config.update(json.loads(mcp_file.read_text(encoding="utf-8")))
        except Exception:
            pass

    # Fallback to opencode.json if neither defines mcp
    if not (
        mcp_config.get("mcp")
        or mcp_config.get("mcpServers")
        or mcp_config.get("mcp_servers")
    ):
        opencode_config = Path.home() / ".config" / "opencode" / "opencode.json"
        if opencode_config.exists():
            try:
                opencode_data = json.loads(opencode_config.read_text(encoding="utf-8"))
                if "mcp" in opencode_data:
                    mcp_config["mcp"] = opencode_data["mcp"]
            except Exception:
                pass

    return load_mcp_servers(mcp_config)


def get_all_mcp_servers_config() -> Dict[str, Dict[str, Any]]:
    """Retrieve full dictionary of configured MCP servers with enabled state."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    config_dir = Path(xdg) / "frea" if xdg else Path.home() / ".config" / "frea"

    mcp_config: Dict[str, Any] = {}
    mcp_file = config_dir / "mcp.json"
    if mcp_file.exists():
        try:
            mcp_config.update(json.loads(mcp_file.read_text(encoding="utf-8")))
        except Exception:
            pass

    if not mcp_config:
        config_file = config_dir / "config.json"
        if config_file.exists():
            try:
                mcp_config.update(json.loads(config_file.read_text(encoding="utf-8")))
            except Exception:
                pass

    if not (
        mcp_config.get("mcp")
        or mcp_config.get("mcpServers")
        or mcp_config.get("mcp_servers")
    ):
        opencode_config = Path.home() / ".config" / "opencode" / "opencode.json"
        if opencode_config.exists():
            try:
                opencode_data = json.loads(opencode_config.read_text(encoding="utf-8"))
                if "mcp" in opencode_data:
                    mcp_config["mcp"] = opencode_data["mcp"]
            except Exception:
                pass

    servers: Dict[str, Any] = (
        mcp_config.get("mcp")
        or mcp_config.get("mcpServers")
        or mcp_config.get("mcp_servers")
        or {}
    )
    result = {}
    for name, spec in servers.items():
        if isinstance(spec, dict):
            s = dict(spec)
            s["enabled"] = s.get("enabled", True) is not False
            result[name] = s
    return result


def toggle_mcp_server(server_name: str) -> bool:
    """Toggle enabled status for specified MCP server and persist to ~/.config/frea/mcp.json.

    Returns the new enabled status.
    """
    xdg = os.environ.get("XDG_CONFIG_HOME")
    config_dir = Path(xdg) / "frea" if xdg else Path.home() / ".config" / "frea"
    config_dir.mkdir(parents=True, exist_ok=True)

    mcp_file = config_dir / "mcp.json"
    mcp_data: Dict[str, Any] = {}
    if mcp_file.exists():
        try:
            mcp_data = json.loads(mcp_file.read_text(encoding="utf-8"))
        except Exception:
            mcp_data = {}

    if not mcp_data.get("mcp"):
        # Copy from all discovered config
        all_specs = get_all_mcp_servers_config()
        mcp_data["mcp"] = all_specs

    servers = mcp_data.setdefault("mcp", {})
    spec = servers.setdefault(server_name, {"type": "local", "enabled": True})
    current_enabled = spec.get("enabled", True) is not False
    new_enabled = not current_enabled
    spec["enabled"] = new_enabled

    try:
        mcp_file.write_text(json.dumps(mcp_data, indent=2), encoding="utf-8")
    except Exception:
        pass

    # Also sync ~/.config/frea/config.json if it has mcp section
    config_file = config_dir / "config.json"
    if config_file.exists():
        try:
            cfg = json.loads(config_file.read_text(encoding="utf-8"))
            if "mcp" in cfg and server_name in cfg["mcp"]:
                cfg["mcp"][server_name]["enabled"] = new_enabled
                config_file.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        except Exception:
            pass

    return new_enabled
