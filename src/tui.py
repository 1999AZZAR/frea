"""Interactive Terminal User Interface (TUI) REPL for Frea styled 1:1 after OpenCode."""

import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, TextIO, Tuple
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.styles import Style
from src.agent import AgentLoop
from src.commands import SessionState, handle_slash_command
from src.ui import (
    THEME,
    Theme,
    console,
    get_header_tokens,
    get_statusline_tokens,
    render_header,
)


class SlashCommandCompleter(Completer):
    """Autocompleter for interactive slash commands."""

    COMMANDS = [
        ("/help", "Display available commands"),
        ("/status", "Show active model and session status"),
        ("/mcp", "Inspect MCP servers and registered tools"),
        ("/skills", "List discovered agent skills"),
        ("/model", "Switch or view current model"),
        ("/compact", "Summarize older messages to free up context"),
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


@dataclass
class TranscriptCard:
    """A card entry in the full-screen interactive transcript."""

    id: int
    kind: str  # "user", "assistant", "tool", "note", "error"
    title: str
    body: str
    collapsed: bool = False
    status: Optional[str] = None
    model: str = ""

    def is_foldable(self) -> bool:
        if self.kind not in ("assistant", "tool", "error"):
            return False
        lines = self.body.splitlines() if self.body else []
        return len(lines) > 2


class OpenCodeTUI:
    """Full-screen interactive TUI for Frea matching Kamui & OpenCode in-place rendering."""

    def __init__(self, repl: "OpenCodeREPL"):
        self.repl = repl
        self.session = repl.session
        self.theme = repl.theme
        self.agent_loop = repl.agent_loop
        self.cards: List[TranscriptCard] = []
        self._next_id: int = 1
        self.hovered_card_id: Optional[int] = None
        self.is_running: bool = False
        self._user_scrolled_line: Optional[int] = None
        self._total_lines: int = 0
        self.app: Optional[Any] = None
        self.input_window: Optional[Any] = None
        self._dialog_floats: List[Any] = []
        self._dialog_kb: Optional[Any] = None
        self._is_dialog_active: bool = False

        from prompt_toolkit.buffer import Buffer

        self.input_buffer: Buffer = Buffer(
            completer=SlashCommandCompleter(),
            multiline=False,
            accept_handler=self._on_input_accept,
        )

    async def show_dialog(self, popup: Any) -> Any:
        """Display a modal dialog overlay directly within OpenCodeTUI's FloatContainer.

        Runs on the existing application event loop without tearing down raw mode
        or alternate screen buffer, ensuring instant recovery when dismissed.
        """
        if not self.app:
            return popup.get_result()

        import asyncio
        from prompt_toolkit.layout import Float

        loop = asyncio.get_running_loop()
        fut: asyncio.Future[Any] = loop.create_future()

        def _close() -> None:
            if not fut.done():
                fut.set_result(popup.get_result())

        widget, focused_el, kb = popup.build_dialog(_close)

        float_el = Float(content=widget, xcursor=False, ycursor=False)
        self._dialog_floats.append(float_el)
        self._dialog_kb = kb
        self._is_dialog_active = True

        if focused_el is not None:
            try:
                self.app.layout.focus(focused_el)
            except Exception:
                pass
        self.app.invalidate()

        try:
            return await fut
        finally:
            self._dialog_floats.clear()
            self._dialog_kb = None
            self._is_dialog_active = False
            if self.input_window is not None:
                try:
                    self.app.layout.focus(self.input_window)
                except Exception:
                    pass
            if self.app:
                self.app.invalidate()

    def _next_card_id(self) -> int:
        cid = self._next_id
        self._next_id += 1
        return cid

    def add_card(
        self,
        kind: str,
        title: str,
        body: str,
        collapsed: bool = False,
        status: Optional[str] = None,
        model: str = "",
    ) -> TranscriptCard:
        card = TranscriptCard(
            id=self._next_card_id(),
            kind=kind,
            title=title,
            body=body,
            collapsed=collapsed,
            status=status,
            model=model,
        )
        self.cards.append(card)
        self._user_scrolled_line = None
        est_lines = (card.body.count("\n") + 2) if card.body else 3
        self._total_lines += est_lines
        return card

    def toggle_card(self, card_id: int) -> bool:
        for card in self.cards:
            if card.id == card_id and card.is_foldable():
                card.collapsed = not card.collapsed
                if self.app:
                    self.app.invalidate()
                return True
        return False

    def toggle_last_foldable(self) -> bool:
        for card in reversed(self.cards):
            if card.is_foldable():
                card.collapsed = not card.collapsed
                if self.app:
                    self.app.invalidate()
                return True
        return False

    def collapse_last(self) -> bool:
        for card in reversed(self.cards):
            if card.is_foldable():
                card.collapsed = True
                if self.app:
                    self.app.invalidate()
                return True
        return False

    def expand_last(self) -> bool:
        for card in reversed(self.cards):
            if card.is_foldable():
                card.collapsed = False
                if self.app:
                    self.app.invalidate()
                return True
        return False

    def set_hovered_card(self, card_id: Optional[int]) -> None:
        if self.hovered_card_id != card_id:
            self.hovered_card_id = card_id
            if self.app:
                self.app.invalidate()

    def scroll_up(self, amount: int = 3) -> None:
        total = max(1, self._total_lines)
        curr = (
            self._user_scrolled_line
            if self._user_scrolled_line is not None
            else (total - 1)
        )
        self._user_scrolled_line = max(0, curr - amount)
        if self.app:
            self.app.invalidate()

    def scroll_down(self, amount: int = 3) -> None:
        if self._user_scrolled_line is not None:
            self._user_scrolled_line += amount
            if self._user_scrolled_line >= self._total_lines - 1:
                self._user_scrolled_line = None
        if self.app:
            self.app.invalidate()

    def _get_cursor_position(self) -> Any:
        from prompt_toolkit.data_structures import Point

        total = max(1, self._total_lines)
        if self._user_scrolled_line is None:
            target = total - 1
        else:
            target = max(0, min(self._user_scrolled_line, total - 1))
        return Point(0, target)

    def _get_transcript_tokens(self) -> List[Tuple[str, str, Any]]:
        from prompt_toolkit.mouse_events import MouseEvent, MouseEventType

        tokens: List[Tuple[str, str, Any]] = []

        def _bg_mouse(e: MouseEvent) -> None:
            if self._is_dialog_active:
                return
            if e.event_type == MouseEventType.SCROLL_UP:
                self.scroll_up(3)
            elif e.event_type == MouseEventType.SCROLL_DOWN:
                self.scroll_down(3)
            elif e.event_type == MouseEventType.MOUSE_MOVE:
                if self.hovered_card_id is not None:
                    self.hovered_card_id = None
                    if self.app:
                        self.app.invalidate()

        # Render greeting header at top of transcript
        tools_cnt, mcp_cnt = self.repl.get_stats()
        header_tokens = get_header_tokens(
            self.session.current_model,
            os.getcwd(),
            tools_count=tools_cnt,
            mcp_count=mcp_cnt,
            theme=self.theme,
        )
        for style, text in header_tokens:
            tokens.append((style, text, _bg_mouse))

        for card in self.cards:
            is_hovered = self.hovered_card_id == card.id
            bg = f"bg:{self.theme.background_panel} " if is_hovered else ""

            def make_card_mouse(cid: int):
                def _card_mouse(e: MouseEvent) -> None:
                    if self._is_dialog_active:
                        return
                    if e.event_type == MouseEventType.MOUSE_DOWN:
                        self.toggle_card(cid)
                    elif e.event_type == MouseEventType.MOUSE_MOVE:
                        if self.hovered_card_id != cid:
                            self.hovered_card_id = cid
                            if self.app:
                                self.app.invalidate()
                    elif e.event_type == MouseEventType.SCROLL_UP:
                        self.scroll_up(3)
                    elif e.event_type == MouseEventType.SCROLL_DOWN:
                        self.scroll_down(3)

                return _card_mouse

            cm = make_card_mouse(card.id)

            if card.kind == "user":
                lines = card.body.splitlines() if card.body else [""]
                tokens.append(("", "\n", cm))
                for line in lines:
                    tokens.append((bg + f"fg:{self.theme.accent}", "▌ ", cm))
                    tokens.append((bg + f"fg:{self.theme.text}", f"{line}\n", cm))

            elif card.kind == "assistant":
                total_lines = len(card.body.splitlines()) if card.body else 0
                model_tag = f"({card.model}) " if card.model else ""

                if card.status:
                    tokens.append((bg + f"fg:{self.theme.primary}", "\n▌ ", cm))
                    if model_tag:
                        tokens.append((bg + f"fg:{self.theme.info}", model_tag, cm))
                    tokens.append(
                        (bg + f"fg:{self.theme.warning}", f"[{card.status}]\n", cm)
                    )
                elif card.collapsed and total_lines > 2:
                    hidden = total_lines - 2
                    tokens.append((bg + f"fg:{self.theme.primary}", "\n▌ ", cm))
                    if model_tag:
                        tokens.append((bg + f"fg:{self.theme.info}", model_tag, cm))
                    pill = f"[▶ Expand (+{hidden} lines) · Ctrl+O / click]"
                    tokens.append(
                        (
                            bg + f"fg:{self.theme.text_muted}",
                            f"{pill}\n",
                            cm,
                        )
                    )
                elif total_lines > 2:
                    tokens.append((bg + f"fg:{self.theme.primary}", "\n▌ ", cm))
                    if model_tag:
                        tokens.append((bg + f"fg:{self.theme.info}", model_tag, cm))
                    pill = "[▼ Collapse · Ctrl+O / click]"
                    tokens.append(
                        (
                            bg + f"fg:{self.theme.text_muted}",
                            f"{pill}\n",
                            cm,
                        )
                    )
                else:
                    tokens.append(("", "\n", cm))

                if card.collapsed and total_lines > 2:
                    lines = card.body.splitlines()
                    for line in lines[:2]:
                        tokens.append((bg + f"fg:{self.theme.primary}", "▌ ", cm))
                        tokens.append((bg + f"fg:{self.theme.text}", f"{line}\n", cm))
                    tokens.append((bg + f"fg:{self.theme.primary}", "▌ ", cm))
                    tokens.append(
                        (
                            bg + f"fg:{self.theme.text_muted}",
                            f"… {total_lines - 2} more line(s) · ctrl+o or click\n",
                            cm,
                        )
                    )
                else:
                    if card.body:
                        for line in card.body.splitlines():
                            tokens.append((bg + f"fg:{self.theme.primary}", "▌ ", cm))
                            tokens.append(
                                (bg + f"fg:{self.theme.text}", f"{line}\n", cm)
                            )

            elif card.kind == "tool":
                lines = card.body.splitlines() if card.body else []
                tokens.append(
                    (bg + f"fg:{self.theme.secondary} bold", f"\n▌ {card.title} ", cm)
                )
                status_style = (
                    f"fg:{self.theme.success}"
                    if "completed" in (card.status or "")
                    else f"fg:{self.theme.warning}"
                )
                tokens.append((bg + status_style, f"[{card.status or ''}]\n", cm))
                if not card.collapsed and lines:
                    for line in lines:
                        tokens.append((bg + f"fg:{self.theme.secondary}", "▌ ", cm))
                        tokens.append(
                            (bg + f"fg:{self.theme.text_muted}", f"{line}\n", cm)
                        )
                elif card.collapsed and lines:
                    tokens.append((bg + f"fg:{self.theme.secondary}", "▌ ", cm))
                    tokens.append(
                        (
                            bg + f"fg:{self.theme.text_muted}",
                            f"… {len(lines)} line(s) output · ctrl+o or click\n",
                            cm,
                        )
                    )

            elif card.kind in ("note", "error"):
                color = (
                    self.theme.error if card.kind == "error" else self.theme.text_muted
                )
                lines = card.body.splitlines() if card.body else [""]
                if len(lines) <= 1:
                    tokens.append((bg + f"fg:{color} bold", f"\n▌ {card.title} ", cm))
                    tokens.append((bg + f"fg:{color}", f"{card.body}\n", cm))
                else:
                    tokens.append((bg + f"fg:{color} bold", f"\n▌ {card.title}\n", cm))
                    for line in lines:
                        tokens.append((bg + f"fg:{color}", f"  {line}\n", cm))

        self._total_lines = sum(text.count("\n") for _, text, *_ in tokens)
        return tokens

    def _on_input_accept(self, buffer: Any) -> bool:
        text = buffer.text.strip()
        if not text:
            return False

        if self.is_running:
            self.add_card(
                "note",
                "Busy",
                "Agent is currently processing a task. Please wait.",
            )
            if self.app:
                self.app.invalidate()
            return True

        buffer.reset()

        if text.startswith("/"):
            if self.app:
                self.app.create_background_task(self._handle_slash_command(text))
            else:
                import asyncio

                asyncio.create_task(self._handle_slash_command(text))
            return True

        if not self.agent_loop:
            self.add_card("error", "Error", "Agent loop is not initialized.")
            if self.app:
                self.app.invalidate()
            return True

        if self.app:
            self.app.create_background_task(self._run_agent_task(text))
        return True

    async def _handle_slash_command(self, text: str) -> None:
        parts = text.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd in ("/exit", "/quit"):
            from src.popup import ConfirmPopup

            popup = ConfirmPopup(title="Exit Frea", message="End this session?")
            confirmed = await self.show_dialog(popup)
            if confirmed and self.app:
                self.app.exit()
            return

        if cmd == "/model":
            if not arg:
                from src.popup import SelectPopup, fetch_gateway_models

                options = fetch_gateway_models()
                popup = SelectPopup(
                    title="Switch Model",
                    options=options,
                    current=self.session.current_model,
                    placeholder="Search models…",
                )
                chosen = await self.show_dialog(popup)
                if chosen:
                    try:
                        self.repl._switch_model(chosen)
                        self.session.current_model = chosen
                        self.add_card("note", "Model", f"Switched model → {chosen}")
                    except Exception as exc:
                        self.add_card(
                            "error", "Error", f"Failed to switch model: {exc}"
                        )
            else:
                try:
                    self.repl._switch_model(arg)
                    self.session.current_model = arg
                    self.add_card("note", "Model", f"Switched model → {arg}")
                except Exception as exc:
                    self.add_card("error", "Error", f"Failed to switch model: {exc}")
            if self.app:
                self.app.invalidate()
            return

        if cmd == "/mcp":
            from src.popup import McpPopup

            popup = McpPopup()
            changed = await self.show_dialog(popup)
            if changed and self.agent_loop and hasattr(self.agent_loop, "executor"):
                self.agent_loop.executor.reload_mcp_servers()
                tools_cnt, mcp_cnt = self.repl.get_stats()
                self.add_card(
                    "note",
                    "MCP",
                    f"Reloaded MCP servers: {mcp_cnt} connected, {tools_cnt} total tools active.",
                )
            if self.app:
                self.app.invalidate()
            return

        if cmd == "/collapse":
            if not self.collapse_last():
                self.add_card("note", "Info", "Nothing to collapse.")
            self._user_scrolled_line = None
            if self.app:
                self.app.invalidate()
            return

        if cmd == "/expand":
            if not self.expand_last():
                self.add_card("note", "Info", "Nothing to expand.")
            self._user_scrolled_line = None
            if self.app:
                self.app.invalidate()
            return

        if cmd == "/clear":
            self.cards.clear()
            self._total_lines = 0
            self._user_scrolled_line = None
            if self.app:
                self.app.invalidate()
            return

        if cmd == "/compact":
            from src.providers import compact_history

            initial_len = len(self.session.history)
            self.session.history = compact_history(
                self.session.history, max_messages=10
            )
            self.add_card(
                "note",
                "Compact",
                f"Compacted history from {initial_len} to {len(self.session.history)} items.",
            )
            self._user_scrolled_line = None
            if self.app:
                self.app.invalidate()
            return

        res = handle_slash_command(text, self.session)
        if res.output:
            self.add_card("note", "Command", res.output)
        if res.exit_requested and self.app:
            self.app.exit()
        self._user_scrolled_line = None
        if self.app:
            self.app.invalidate()

    async def _run_agent_task(self, text: str) -> None:
        import asyncio

        self.is_running = True
        self._user_scrolled_line = None

        self.add_card("user", "You", text)
        asst_card = self.add_card(
            "assistant",
            "Assistant",
            "",
            status=f"⠋ Thinking… ({self.session.current_model})",
            model=self.session.current_model,
        )
        if self.app:
            self.app.invalidate()

        spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

        async def _spinner_ticker() -> None:
            idx = 0
            while self.is_running:
                frame = spinner_frames[idx % len(spinner_frames)]
                idx += 1
                if asst_card.status and "…" in asst_card.status:
                    pure = asst_card.status.lstrip("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏ ")
                    asst_card.status = f"{frame} {pure}"
                if self.app:
                    self.app.invalidate()
                await asyncio.sleep(0.08)

        ticker_task = asyncio.create_task(_spinner_ticker())

        def on_call(name: str, args: Dict[str, Any]) -> None:
            asst_card.status = f"⠋ Running {name}…"
            args_str = " ".join(f"{k}={v}" for k, v in args.items())
            self.add_card(
                "tool", f"$ {name} {args_str}".strip(), "", status="⠋ running…"
            )
            self._user_scrolled_line = None
            if self.app:
                self.app.invalidate()

        def on_result(name: str, args: Dict[str, Any], result: str) -> None:
            asst_card.status = f"⠋ Processing… ({self.session.current_model})"
            for c in reversed(self.cards):
                if c.kind == "tool" and c.status and "running" in c.status:
                    c.status = "✓ completed"
                    c.body = result
                    c.collapsed = True
                    break
            self._user_scrolled_line = None
            if self.app:
                self.app.invalidate()

        old_on_call = getattr(self.agent_loop, "on_tool_call", None)
        old_on_res = getattr(self.agent_loop, "on_tool_result", None)
        self.agent_loop.on_tool_call = on_call
        self.agent_loop.on_tool_result = on_result

        try:
            agent_result = await asyncio.to_thread(self.agent_loop.run, text)
            asst_card.body = agent_result.final_answer
            asst_card.status = None
            asst_card.collapsed = self.session.response_collapsed
            self.session.record_turn(text, agent_result.final_answer)
        except Exception as exc:
            asst_card.status = None
            self.add_card("error", "Error", str(exc))
        finally:
            self.is_running = False
            ticker_task.cancel()
            self.agent_loop.on_tool_call = old_on_call
            self.agent_loop.on_tool_result = old_on_res
            self._user_scrolled_line = None
            if self.app:
                self.app.invalidate()

    def run(self) -> int:
        from prompt_toolkit.application import Application
        from prompt_toolkit.filters import Condition
        from prompt_toolkit.key_binding import DynamicKeyBindings, KeyBindings, merge_key_bindings
        from prompt_toolkit.layout import FloatContainer, HSplit, Layout, VSplit, Window
        from prompt_toolkit.layout.containers import WindowAlign
        from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl

        @Condition
        def _not_dialog() -> bool:
            return not self._is_dialog_active

        def _get_dialog_kb() -> Optional[KeyBindings]:
            return self._dialog_kb

        kb = KeyBindings()

        @kb.add("c-o", filter=_not_dialog)
        def _toggle_fold(event: Any) -> None:
            self.toggle_last_foldable()

        @kb.add("c-c", filter=_not_dialog)
        def _cancel(event: Any) -> None:
            if self.input_buffer.text:
                self.input_buffer.reset()
            else:
                event.app.exit()

        @kb.add("c-d", filter=_not_dialog)
        def _eof(event: Any) -> None:
            if not self.input_buffer.text:
                event.app.exit()

        @kb.add("pageup", filter=_not_dialog)
        def _pageup(event: Any) -> None:
            self.scroll_up(10)

        @kb.add("pagedown", filter=_not_dialog)
        def _pagedown(event: Any) -> None:
            self.scroll_down(10)

        app_kb = merge_key_bindings([DynamicKeyBindings(_get_dialog_kb), kb])

        tools_cnt, mcp_cnt = self.repl.get_stats()

        transcript_control = FormattedTextControl(
            self._get_transcript_tokens,
            focusable=False,
            get_cursor_position=self._get_cursor_position,
        )

        transcript_window = Window(
            content=transcript_control,
            wrap_lines=True,
            always_hide_cursor=True,
        )

        self.input_window = Window(BufferControl(buffer=self.input_buffer), height=1)

        prompt_window = VSplit(
            [
                Window(
                    FormattedTextControl([("class:prompt", "❯ ")]),
                    width=2,
                    dont_extend_width=True,
                ),
                self.input_window,
            ]
        )

        def get_left_status() -> List[Tuple[str, str]]:
            l_toks, _ = get_statusline_tokens(
                os.getcwd(),
                model=self.session.current_model,
                tools_count=tools_cnt,
                mcp_count=mcp_cnt,
                theme=self.theme,
            )
            return l_toks

        def get_right_status() -> List[Tuple[str, str]]:
            _, r_toks = get_statusline_tokens(
                os.getcwd(),
                model=self.session.current_model,
                tools_count=tools_cnt,
                mcp_count=mcp_cnt,
                theme=self.theme,
            )
            return r_toks

        status_left = Window(
            content=FormattedTextControl(get_left_status),
            align=WindowAlign.LEFT,
            height=1,
            style=f"bg:{self.theme.background_panel}",
        )
        status_right = Window(
            content=FormattedTextControl(get_right_status),
            align=WindowAlign.RIGHT,
            height=1,
            style=f"bg:{self.theme.background_panel}",
        )
        status_bar = VSplit([status_left, status_right], height=1)

        root = HSplit(
            [
                transcript_window,
                Window(height=1, char="─", style=f"fg:{self.theme.border_subtle}"),
                prompt_window,
                status_bar,
            ]
        )

        float_container = FloatContainer(
            content=root,
            floats=self._dialog_floats,
        )

        from src.popup import POPUP_STYLE_DICT

        pt_style = Style.from_dict(
            {
                "prompt": f"{self.theme.primary} bold",
                **POPUP_STYLE_DICT,
            }
        )

        self.app = Application(
            layout=Layout(float_container, focused_element=self.input_window),
            key_bindings=app_kb,
            style=pt_style,
            mouse_support=True,
            full_screen=True,
        )

        try:
            self.app.run()
        except (KeyboardInterrupt, EOFError):
            pass
        return 0


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
        from prompt_toolkit.key_binding import KeyBindings

        kb = KeyBindings()

        @kb.add("c-o")
        def _toggle_fold(event: Any) -> None:
            self.session.response_collapsed = not self.session.response_collapsed
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

        # Full-screen interactive TUI (Kamui & OpenCode parity)
        tui = OpenCodeTUI(self)
        return tui.run()


InteractiveREPL = OpenCodeREPL
