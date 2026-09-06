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
  /status             - View session status and active model
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
        status_info = (
            f"Model: {session.current_model}\n"
            f"Provider: {session.current_provider}\n"
            f"History: {len(session.history)} messages ({turns} turns)\n"
            f"Tools: 6 active tools (bash_run, file_read, file_write, file_patch, grep_search, find_files)"
        )
        return CommandResult(handled=True, output=status_info)
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
