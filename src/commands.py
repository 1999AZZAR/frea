"""Interactive slash commands and session management for Frea harness."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
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
    on_model_switch: Optional[Callable[[str], None]] = field(
        default=None, repr=False, compare=False
    )

    def record_turn(self, user: str, assistant: str) -> None:
        self.history.append({"role": "user", "content": user})
        self.history.append({"role": "assistant", "content": assistant})


HELP_TEXT = """Available commands:
  /help                 - Display this help message
  /status               - View session status, MCP servers, and active model
  /mcp                  - Inspect MCP servers and registered tools
  /skills               - List discovered agent skills
  /model <name>         - View or switch current model
  /clear                - Clear terminal screen
  /compact              - Compress conversation history
  /exit or /quit        - Exit interactive session
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
                client.stop()
        except Exception:
            pass

        skills_list = []
        try:
            from src.skills import discover_skills

            skills = discover_skills()
            for s_name in skills:
                skills_list.append(s_name)
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
    elif cmd == "/mcp":
        try:
            from src.mcp import load_user_mcp_servers

            servers = load_user_mcp_servers()
            if not servers:
                return CommandResult(
                    handled=True,
                    output=(
                        "No MCP servers connected.\n"
                        "Configure MCP servers under 'mcpServers' in ~/.config/frea/config.json"
                    ),
                )

            lines = [f"MCP Servers ({len(servers)}):"]
            for name, client in servers.items():
                is_conn = client.is_connected()
                status_text = "Connected" if is_conn else "Disconnected"
                lines.append(f"  • {name} [{status_text}]")
                try:
                    tools = client.list_tools()
                    if tools:
                        lines.append(f"    Tools ({len(tools)}):")
                        for t in tools:
                            t_name = t.get("name", "unknown")
                            t_desc = (t.get("description") or "").split("\n")[0]
                            desc_str = f" - {t_desc}" if t_desc else ""
                            lines.append(f"      • {t_name}{desc_str}")
                    else:
                        lines.append("    No tools advertised")
                except Exception as err:
                    lines.append(f"    Error listing tools: {err}")
                finally:
                    client.stop()

            return CommandResult(handled=True, output="\n".join(lines))

        except Exception as exc:
            return CommandResult(
                handled=True, output=f"Failed to inspect MCP servers: {exc}"
            )
    elif cmd in ("/skills", "/skill"):
        try:
            from src.skills import discover_skills

            skills = discover_skills()
            if not skills:
                return CommandResult(
                    handled=True,
                    output="No skills found in .agents/skills, ~/.config/frea/skills, or ~/.agents/skills",
                )

            lines = [f"Available Skills ({len(skills)}):"]
            for s_name, s_info in skills.items():
                lines.append(f"  • {s_name}: {s_info.description}")
            return CommandResult(handled=True, output="\n".join(lines))

        except Exception as exc:
            return CommandResult(
                handled=True, output=f"Failed to discover skills: {exc}"
            )
    elif cmd in ("/exit", "/quit"):
        return CommandResult(
            handled=True, exit_requested=True, output="Exiting Frea session."
        )
    elif cmd == "/clear":
        return CommandResult(handled=True, output="\033[2J\033[H")
    elif cmd == "/model":
        if arg:
            old = session.current_model
            session.current_model = arg
            if session.on_model_switch:
                try:
                    session.on_model_switch(arg)
                except Exception as exc:
                    session.current_model = old
                    return CommandResult(
                        handled=True,
                        output=f"Failed to switch model: {exc}",
                    )
            return CommandResult(handled=True, output=f"Switched model → {arg}")
        preset_lines = [
            f"Current model: {session.current_model}",
            "",
            "Presets (free / no key required):",
            "  openrouter/auto              - OpenRouter smart routing",
            "  kimi-k2.5-free               - Kimi K2.5 via opencode gateway",
            "  kilocode/kilo-auto/balanced  - KiloCode balanced routing",
            "",
            "Usage: /model <name>",
        ]
        return CommandResult(handled=True, output="\n".join(preset_lines))
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
