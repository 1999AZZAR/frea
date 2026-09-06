"""Interactive Terminal User Interface (TUI) REPL for Frea styled 1:1 after OpenCode."""

import os
import sys
from typing import Any, Dict, Iterable, Optional, TextIO, Tuple
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.styles import Style
from src.agent import AgentLoop
from src.commands import SessionState, handle_slash_command
from src.ui import THEME, Theme, console, render_header, render_statusline


class SlashCommandCompleter(Completer):
    """Autocompleter for interactive slash commands."""

    COMMANDS = [
        ("/help", "Display available commands"),
        ("/status", "Show active model and session status"),
        ("/model", "Switch or view current model"),
        ("/compact", "Compress conversation history"),
        ("/clear", "Clear terminal screen"),
        ("/exit", "Exit interactive session"),
        ("/quit", "Exit interactive session"),
    ]

    def get_completions(
        self, document: Document, complete_event: Optional[CompleteEvent]
    ) -> Iterable[Completion]:
        text = document.text_before_cursor.strip()
        if not text.startswith("/"):
            return

        for cmd, meta in self.COMMANDS:
            if cmd.startswith(text.lower()):
                yield Completion(cmd, start_position=-len(text), display_meta=meta)


class OpenCodeREPL:
    """OpenCode-styled REPL for interactive Frea sessions."""

    def __init__(
        self,
        agent_loop: Optional[AgentLoop] = None,
        agent: Optional[AgentLoop] = None,
        session: Optional[SessionState] = None,
        session_state: Optional[SessionState] = None,
        theme: Theme = THEME,
    ):
        self.agent_loop = agent_loop or agent
        self.session = session or session_state or SessionState()
        self.theme = theme
        self._active_out_stream: Optional[TextIO] = None

        # Wire live tool execution streaming into agent loop
        if self.agent_loop:
            if not getattr(self.agent_loop, "on_tool_call", None):
                self.agent_loop.on_tool_call = self._on_tool_call
            if not getattr(self.agent_loop, "on_tool_result", None):
                self.agent_loop.on_tool_result = self._on_tool_result

    def _on_tool_call(self, name: str, args: Dict[str, Any]) -> None:
        from src.cards import render_tool_call

        banner = render_tool_call(name, args, theme=self.theme)
        if self._active_out_stream and self._active_out_stream != sys.stdout:
            self._active_out_stream.write(f"{banner}\n")
            self._active_out_stream.flush()
        else:
            console.print(banner)

    def _on_tool_result(self, name: str, args: Dict[str, Any], result: str) -> None:
        from src.cards import render_tool_result

        banner = render_tool_result(name, args, result, theme=self.theme)
        if self._active_out_stream and self._active_out_stream != sys.stdout:
            self._active_out_stream.write(f"{banner}\n")
            self._active_out_stream.flush()
        else:
            console.print(banner)

    def get_stats(self) -> Tuple[int, int]:
        """Compute active tools count and connected MCP servers count."""
        tools_count = 11
        mcp_count = 0
        if (
            self.agent_loop
            and hasattr(self.agent_loop, "executor")
            and hasattr(self.agent_loop.executor, "registry")
        ):
            reg = self.agent_loop.executor.registry
            if hasattr(reg, "_tools"):
                tools_count = len(reg._tools)
            if hasattr(reg, "_mcp_clients"):
                mcp_count = len(reg._mcp_clients)
        return tools_count, mcp_count

    def get_prompt_tokens(self) -> list[tuple[str, str]]:
        """Return styled prompt tokens for prompt_toolkit."""
        return [("class:prompt", "❯ ")]

    def get_status_display(self) -> str:
        """Return formatted status text for the active session."""
        res = handle_slash_command("/status", self.session)
        return res.output or ""

    def handle_input(self, line: str) -> Tuple[bool, str]:
        """Process a single input line, dispatching to slash commands or agent loop."""
        text = line.strip()
        if not text:
            return False, ""

        if text.startswith("/"):
            res = handle_slash_command(text, self.session)
            return res.exit_requested, res.output or ""

        if not self.agent_loop:
            return False, "Agent loop is not initialized."

        agent_result = self.agent_loop.run(text)
        self.session.record_turn(text, agent_result.final_answer)
        return False, agent_result.final_answer

    def run_repl(
        self,
        input_stream: Optional[TextIO] = None,
        output_stream: Optional[TextIO] = None,
    ) -> int:
        """Run interactive loop until exit requested or EOF reached."""
        in_stream = input_stream or sys.stdin
        out_stream = output_stream or sys.stdout
        self._active_out_stream = out_stream
        tools_cnt, mcp_cnt = self.get_stats()

        # Stream fallback for non-tty/unit testing
        if input_stream is not None or not sys.stdin.isatty():
            header = render_header(
                self.session.current_model,
                os.getcwd(),
                tools_count=tools_cnt,
                mcp_count=mcp_cnt,
                theme=self.theme,
            )
            out_stream.write(f"{header}\n")
            out_stream.flush()

            while True:
                try:
                    out_stream.write(f"\n[{self.session.current_model}] frea ❯ ")
                    out_stream.flush()

                    line = in_stream.readline()
                    if not line:
                        break

                    should_exit, message = self.handle_input(line)
                    if message:
                        out_stream.write(f"\n{message}\n")
                        out_stream.flush()

                    if should_exit:
                        break
                except (KeyboardInterrupt, EOFError):
                    out_stream.write("\nSession interrupted. Exiting.\n")
                    out_stream.flush()
                    break
            return 0

        # Full OpenCode interactive mode
        header_text = render_header(
            self.session.current_model,
            os.getcwd(),
            tools_count=tools_cnt,
            mcp_count=mcp_cnt,
            theme=self.theme,
        )
        console.print(header_text)

        pt_style = Style.from_dict(
            {
                "prompt": f"{self.theme.primary} bold",
                "bottom-toolbar": f"bg:{self.theme.background_panel} {self.theme.text_muted}",
            }
        )

        prompt_session: PromptSession[str] = PromptSession(
            completer=SlashCommandCompleter(),
            style=pt_style,
        )

        while True:
            try:
                statusline = render_statusline(
                    os.getcwd(),
                    model=self.session.current_model,
                    tools_count=tools_cnt,
                    mcp_count=mcp_cnt,
                    theme=self.theme,
                )
                user_input = prompt_session.prompt(
                    self.get_prompt_tokens(),
                    bottom_toolbar=lambda: statusline,
                )

                should_exit, message = self.handle_input(user_input)
                if message:
                    console.print(message)

                if should_exit:
                    break
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]Session interrupted. Exiting.[/]")
                break

        return 0


InteractiveREPL = OpenCodeREPL
