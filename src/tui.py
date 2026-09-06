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
        ("/mcp", "Inspect MCP servers and registered tools"),
        ("/skills", "List discovered agent skills"),
        ("/model", "Switch or view current model"),
        ("/compact", "Fold response into compact peek"),
        ("/collapse", "Fold response into compact peek"),
        ("/expand", "Expand folded response into full view"),
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
        self._current_status: Optional[Any] = None

        # Register model switcher so /model propagates to live provider
        self.session.on_model_switch = self._switch_model

        # Wire live tool execution streaming into agent loop
        if self.agent_loop:
            if not getattr(self.agent_loop, "on_tool_call", None):
                self.agent_loop.on_tool_call = self._on_tool_call
            if not getattr(self.agent_loop, "on_tool_result", None):
                self.agent_loop.on_tool_result = self._on_tool_result

    def _switch_model(self, model_name: str) -> None:
        """Hot-swap the underlying provider when the user types /model <name>."""
        from src.providers import get_provider

        # Detect provider family from model name
        if "openrouter" in model_name.lower():
            provider_key = "openrouter"
        elif "/" in model_name:
            provider_key = model_name.split("/")[0]
        else:
            provider_key = model_name  # e.g. "kimi-k2.5-free" → OpencodeProvider

        new_provider = get_provider(provider_key, model=model_name)
        if self.agent_loop:
            self.agent_loop.provider = new_provider
        self.session.current_provider = provider_key

    def _on_tool_call(self, name: str, args: Dict[str, Any]) -> None:
        from src.cards import render_tool_call

        if self._current_status:
            self._current_status.update(
                f"[bold {self.theme.secondary}]Running[/] [dim]{name}…[/]"
            )

        banner = render_tool_call(name, args, theme=self.theme)
        if self._active_out_stream and self._active_out_stream != sys.stdout:
            self._active_out_stream.write(f"{banner}\n")
            self._active_out_stream.flush()
        else:
            console.print(banner)

    def _on_tool_result(self, name: str, args: Dict[str, Any], result: str) -> None:
        from src.cards import render_tool_result

        if self._current_status:
            self._current_status.update(
                f"[bold {self.theme.primary}]Processing response…[/] [dim]({self.session.current_model})[/]"
            )

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
            parts = text.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1].strip() if len(parts) > 1 else ""

            # /model with no arg → interactive popup picker
            if cmd == "/model" and not arg and sys.stdin.isatty():
                from src.popup import model_select_popup

                chosen = model_select_popup(self.session.current_model)
                if chosen:
                    try:
                        self._switch_model(chosen)
                        self.session.current_model = chosen
                        return False, f"Switched model → {chosen}"
                    except Exception as exc:
                        return False, f"Failed to switch model: {exc}"
                return False, ""

            # /mcp with tty → interactive MCP manager popup
            if cmd == "/mcp" and sys.stdin.isatty():
                from src.popup import mcp_popup

                changed = mcp_popup()
                if changed and self.agent_loop and hasattr(self.agent_loop, "executor"):
                    self.agent_loop.executor.reload_mcp_servers()
                    tools_cnt, mcp_cnt = self.get_stats()
                    return (
                        False,
                        f"Reloaded MCP servers: {mcp_cnt} connected, {tools_cnt} total tools active.",
                    )
                return False, ""

            # /exit / /quit with tty → confirm popup
            if cmd in ("/exit", "/quit") and sys.stdin.isatty():
                from src.popup import ConfirmPopup

                confirmed = ConfirmPopup(
                    title="Exit Frea",
                    message="End this session?",
                ).run()
                if confirmed:
                    return True, "Exiting Frea session."
                return False, ""

            res = handle_slash_command(text, self.session)
            return res.exit_requested, res.output or ""

        if not self.agent_loop:
            return False, "Agent loop is not initialized."

        # Active loading / thinking / processing indicator for interactive REPL
        if sys.stdin.isatty() and (
            not self._active_out_stream or self._active_out_stream == sys.stdout
        ):
            with console.status(
                f"[bold {self.theme.primary}]Thinking…[/] [dim]({self.session.current_model})[/]",
                spinner="dots",
                spinner_style=f"bold {self.theme.primary}",
            ) as status:
                self._current_status = status
                try:
                    agent_result = self.agent_loop.run(text)
                finally:
                    self._current_status = None
        else:
            agent_result = self.agent_loop.run(text)

        self.session.record_turn(text, agent_result.final_answer)
        from src.cards import render_response_card

        card = render_response_card(
            agent_result.final_answer,
            collapsed=self.session.response_collapsed,
            model=self.session.current_model,
            theme=self.theme,
        )
        return False, card

    def _build_key_bindings(self) -> Any:
        """Create prompt_toolkit KeyBindings supporting Ctrl+O response fold/expand."""
        from prompt_toolkit.application import run_in_terminal
        from prompt_toolkit.key_binding import KeyBindings

        kb = KeyBindings()

        @kb.add("c-o")
        def _toggle_fold(event: Any) -> None:
            self.session.response_collapsed = not self.session.response_collapsed
            if self.session.last_response:
                from src.cards import render_response_card

                card = render_response_card(
                    self.session.last_response,
                    collapsed=self.session.response_collapsed,
                    model=self.session.current_model,
                    theme=self.theme,
                )
                run_in_terminal(lambda: console.print(card))
            else:
                mode = "Compact" if self.session.response_collapsed else "Expanded"
                run_in_terminal(
                    lambda: console.print(
                        f"[{self.theme.text_muted}]{mode} mode enabled. No previous response to display.[/]"
                    )
                )
            event.app.invalidate()

        return kb

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
            key_bindings=self._build_key_bindings(),
        )
        while True:
            try:
                user_input = prompt_session.prompt(
                    self.get_prompt_tokens(),
                    bottom_toolbar=lambda: render_statusline(
                        os.getcwd(),
                        model=self.session.current_model,
                        tools_count=tools_cnt,
                        mcp_count=mcp_cnt,
                        theme=self.theme,
                    ),
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
