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
    current_model: str = "kilo-auto/free"
    current_provider: str = "kilo"
    history: List[Dict[str, Any]] = field(default_factory=list)
    response_collapsed: bool = False
    last_response: str = ""

    on_model_switch: Optional[Callable[[str], None]] = field(
        default=None, repr=False, compare=False
    )

    def record_turn(self, user: str, assistant: str) -> None:
        self.history.append({"role": "user", "content": user})
        self.history.append({"role": "assistant", "content": assistant})
        self.last_response = assistant


HELP_TEXT = """Available commands:
  /help                 - Display this help message
  /status               - View session status, MCP servers, and active model
  /mcp                  - Inspect and toggle MCP servers
  /skills               - List discovered agent skills
  /model <name>         - View or switch current model
  /expand               - Expand folded response (full view)
  /collapse             - Fold response into compact peek
  /compact              - Summarize older messages to free up context
  /clear                - Clear terminal screen
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
            from src.mcp import get_all_mcp_servers_config

            specs = get_all_mcp_servers_config()
            for name, spec in specs.items():
                status = "Connected" if spec.get("enabled", True) else "Disabled"
                mcp_servers.append((name, status))
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
            from src.mcp import get_all_mcp_servers_config

            specs = get_all_mcp_servers_config()
            if not specs:
                return CommandResult(
                    handled=True,
                    output=(
                        "No MCP servers connected.\n"
                        "Configure MCP servers under 'mcpServers' in ~/.config/frea/config.json"
                    ),
                )

            lines = [f"MCP Servers ({len(specs)}):"]
            for name, spec in specs.items():
                status_text = (
                    "Connected" if spec.get("enabled", True) else "Disabled"
                )
                lines.append(f"  • {name} [{status_text}]")

            return CommandResult(handled=True, output="\n".join(lines))
        except Exception as e:
            return CommandResult(
                handled=True, output=f"Failed to inspect MCP servers: {e}"
            )

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
    elif cmd == "/expand":
        session.response_collapsed = False
        return CommandResult(
            handled=True,
            output="Expanded response."
            if session.last_response
            else "Nothing to expand.",
        )
    elif cmd == "/collapse":
        session.response_collapsed = True
        return CommandResult(
            handled=True,
            output="Collapsed response."
            if session.last_response
            else "Nothing to collapse.",
        )
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
