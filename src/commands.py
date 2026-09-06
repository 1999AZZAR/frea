"""Interactive slash commands and session management for Frea harness."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from src.providers import compact_history


@dataclass
class CommandResult:
    handled: bool
    exit_requested: bool = False
    output: Optional[str] = None


@dataclass
class SessionState:
    current_model: str = "openrouter/auto"
    current_provider: str = "openrouter"
    history: List[Dict[str, Any]] = field(default_factory=list)

    def record_turn(self, user: str, assistant: str) -> None:
        self.history.append({"role": "user", "content": user})
        self.history.append({"role": "assistant", "content": assistant})


HELP_TEXT = """Available commands:
  /help               - Display this help message
  /status             - View session status, MCP servers, and active model
  /model [name]       - View or switch current model
  /clear              - Clear terminal screen
  /compact            - Compress conversation history
  /exit or /quit      - Exit interactive session
"""


def handle_slash_command(user_input: str, session: SessionState) -> CommandResult:
    """Evaluate slash commands entered during interactive session."""
    text = user_input.strip()
    if not text.startswith("/"):
        return CommandResult(handled=False)

    parts = text.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd == "/help":
        return CommandResult(handled=True, output=HELP_TEXT)
    elif cmd == "/status":
        turns = len(session.history) // 2
        mcp_servers = []
        try:
            from src.mcp import load_user_mcp_servers

            servers = load_user_mcp_servers()
            for name, client in servers.items():
                status = "Connected" if client.is_connected() else "Disconnected"
                mcp_servers.append((name, status))
        except Exception:
            pass

        skills_list = []
        try:
            from src.skills import discover_skills

            skills = discover_skills()
            for s in skills:
                skills_list.append(s.name)
        except Exception:
            pass

        status_lines = [
            f"Model: {session.current_model}",
            f"Provider: {session.current_provider}",
            f"History: {len(session.history)} messages ({turns} turns)",
            "Tools: 11 active tools (read_file, write_file, patch_file, list_directory, grep, glob, run_command, command_status, stop_command, update_plan, skill)",
        ]

        if mcp_servers:
            status_lines.append(f"MCP Servers ({len(mcp_servers)}):")
            for name, status in mcp_servers:
                status_lines.append(f"  • {name} [{status}]")
        else:
            status_lines.append("MCP: No servers connected")

        if skills_list:
            status_lines.append(f"Skills ({len(skills_list)} available):")
            for s_name in skills_list[:6]:
                status_lines.append(f"  • {s_name}")
            if len(skills_list) > 6:
                status_lines.append(f"  ... ({len(skills_list) - 6} more)")

        return CommandResult(handled=True, output="\n".join(status_lines))
    elif cmd in ("/exit", "/quit"):
        return CommandResult(
            handled=True, exit_requested=True, output="Exiting Frea session."
        )
    elif cmd == "/clear":
        return CommandResult(handled=True, output="\033[2J\033[H")
    elif cmd == "/model":
        if arg:
            session.current_model = arg
            return CommandResult(handled=True, output=f"Switched model to: {arg}")
        return CommandResult(
            handled=True, output=f"Current model: {session.current_model}"
        )
    elif cmd == "/compact":
        initial_len = len(session.history)
        session.history = compact_history(session.history, max_messages=10)
        return CommandResult(
            handled=True,
            output=f"Compacted history from {initial_len} to {len(session.history)} items.",
        )
    else:
        return CommandResult(
            handled=True,
            output=f"Unknown command: {cmd}. Type /help for available options.",
        )
