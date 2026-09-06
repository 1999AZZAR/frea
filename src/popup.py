"""
Popup / dialog system for Frea TUI — OpenCode-style floating overlays.

Provides four primitives:
  SelectPopup   — fuzzy-searchable picker (↑↓/Enter/Esc)
  ConfirmPopup  — yes/no confirmation
  AlertPopup    — informational message
  InputPopup    — single-line freeform input

All run as a nested prompt_toolkit Application that blocks until dismissed,
returns the user's choice, and restores the parent terminal state cleanly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, Iterable, List, Optional, TypeVar

from prompt_toolkit import Application
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from prompt_toolkit.layout import (
    ConditionalContainer,
    Float,
    FloatContainer,
    HSplit,
    Layout,
    VSplit,
    Window,
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Box, Frame, Label, TextArea

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Shared style — matches Frea's OpenCode-derived color palette
# ---------------------------------------------------------------------------

POPUP_STYLE = Style.from_dict(
    {
        # Dim backdrop via bg color on outermost container
        "popup-backdrop": "bg:#0a0a0a",
        # Dialog frame / panel
        "frame.border": "#504945",
        "frame.label": "#d4be98 bold",
        # List items
        "select-item": "#d4be98",
        "select-item.focused": "bg:#d4be98 #1d2021 bold",
        "select-item.current": "#d8a657 bold",
        "select-category": "#a89984 bold",
        # Search input
        "search-label": "#a89984",
        "search-input": "#d4be98",
        "search-cursor": "#d8a657",
        # Footer hints
        "hint-key": "#a89984",
        "hint-label": "#504945",
        # Confirm dialog buttons
        "btn": "#a89984",
        "btn.focused": "bg:#d4be98 #1d2021 bold",
        "btn.yes": "#89b482",
        "btn.no": "#ea6962",
        # Alert
        "alert-text": "#d4be98",
    }
)


# ---------------------------------------------------------------------------
# SelectPopup — fuzzy-searchable list picker
# ---------------------------------------------------------------------------


@dataclass
class SelectOption(Generic[T]):
    label: str
    value: T
    description: str = ""
    category: str = ""


class SelectPopup(Generic[T]):
    """
    Full-screen floating picker with fuzzy search, category grouping,
    ↑↓ navigation, Enter to select, Esc/Ctrl+C to cancel.

    Returns the chosen value, or ``None`` if cancelled.
    """

    def __init__(
        self,
        title: str,
        options: List[SelectOption[T]],
        current: Optional[T] = None,
        placeholder: str = "Search…",
        on_select: Optional[Callable[[T], None]] = None,
    ) -> None:
        self.title = title
        self._all_options = options
        self._current = current
        self.placeholder = placeholder
        self._on_select = on_select

        self._result: Optional[T] = None
        self._cancelled = True

        # Mutable state
        self._filter = ""
        self._cursor = 0
        self._filtered: List[SelectOption[T]] = list(options)

        # Pre-select current if provided
        if current is not None:
            for i, opt in enumerate(self._filtered):
                if opt.value == current:
                    self._cursor = i
                    break

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_filter(self, query: str) -> None:
        self._filter = query
        q = query.lower().strip()
        if not q:
            self._filtered = list(self._all_options)
        else:
            self._filtered = [
                o
                for o in self._all_options
                if q in o.label.lower()
                or q in o.description.lower()
                or q in o.category.lower()
            ]
        self._cursor = 0

    def _move(self, delta: int) -> None:
        if not self._filtered:
            return
        self._cursor = (self._cursor + delta) % len(self._filtered)

    def _build_list_text(self) -> List[tuple[str, str]]:
        """Return formatted-text tokens for the option list."""
        tokens: List[tuple[str, str]] = []
        prev_cat = None

        for i, opt in enumerate(self._filtered):
            # Category header
            if opt.category and opt.category != prev_cat:
                tokens.append(("class:select-category", f"  {opt.category}\n"))
                prev_cat = opt.category

            is_focused = i == self._cursor
            is_current = opt.value == self._current
            style = (
                "class:select-item.focused"
                if is_focused
                else ("class:select-item.current" if is_current else "class:select-item")
            )
            prefix = "● " if is_current and not is_focused else "  "
            label = opt.label
            desc = f"  {opt.description}" if opt.description else ""
            tokens.append((style, f"{prefix}{label}"))
            if desc:
                tokens.append(("class:hint-key", desc))
            tokens.append(("", "\n"))

        if not self._filtered:
            tokens.append(("class:hint-key", "  No results\n"))

        return tokens

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> Optional[T]:
        """Block until user selects or cancels. Returns value or None."""
        search_area = TextArea(
            text="",
            multiline=False,
            prompt=HTML("<hint-label>  Search  </hint-label>"),
            style="class:search-input",
            focus_on_click=True,
        )

        list_control = FormattedTextControl(
            text=self._build_list_text, focusable=False
        )

        kb_global = KeyBindings()
        kb_search = KeyBindings()

        @kb_search.add("up")
        @kb_search.add("c-p")
        def _up(event: Any) -> None:
            self._move(-1)
            list_control.text = self._build_list_text  # type: ignore[assignment]

        @kb_search.add("down")
        @kb_search.add("c-n")
        def _down(event: Any) -> None:
            self._move(1)
            list_control.text = self._build_list_text  # type: ignore[assignment]

        @kb_search.add("enter")
        def _enter(event: Any) -> None:
            if self._filtered:
                chosen = self._filtered[self._cursor]
                self._result = chosen.value
                self._cancelled = False
                if self._on_select:
                    self._on_select(chosen.value)
            event.app.exit()

        @kb_global.add("escape")
        @kb_global.add("c-c")
        @kb_global.add("c-q")
        def _cancel(event: Any) -> None:
            self._cancelled = True
            event.app.exit()

        # Wire search input → filter
        def _on_text_changed(_: Any) -> None:
            self._apply_filter(search_area.text)
            list_control.text = self._build_list_text  # type: ignore[assignment]

        search_area.buffer.on_text_changed += _on_text_changed  # type: ignore[operator]

        # Layout: title bar + search + scrollable list + footer hint
        title_bar = Window(
            content=FormattedTextControl(
                text=lambda: [("class:frame.label", f"  {self.title}  ")]
            ),
            height=1,
            style="class:frame.label",
        )
        sep = Window(height=1, char="─", style="class:frame.border")
        search_win = Box(
            body=search_area,
            padding_left=2,
            padding_right=2,
            height=1,
        )
        list_win = Window(
            content=list_control,
            height=12,
            scroll_offsets=None,  # type: ignore[arg-type]
        )
        hint_win = Window(
            content=FormattedTextControl(
                text=lambda: [
                    ("class:hint-key", "  ↑↓"),
                    ("class:hint-label", " navigate  "),
                    ("class:hint-key", "Enter"),
                    ("class:hint-label", " select  "),
                    ("class:hint-key", "Esc"),
                    ("class:hint-label", " cancel  "),
                ]
            ),
            height=1,
        )

        dialog_body = Frame(
            body=HSplit(
                [
                    title_bar,
                    sep,
                    search_win,
                    list_win,
                    hint_win,
                ]
            ),
            style="class:frame.border",
        )

        # Float the dialog in the center of the screen
        root_container = FloatContainer(
            content=Window(style="class:popup-backdrop"),
            floats=[
                Float(
                    content=dialog_body,
                    xcursor=False,
                    ycursor=False,
                )
            ],
        )

        app: Application[None] = Application(
            layout=Layout(root_container, focused_element=search_area),
            key_bindings=merge_key_bindings([kb_global, kb_search]),
            style=POPUP_STYLE,
            mouse_support=True,
            full_screen=True,
        )
        app.run()
        return None if self._cancelled else self._result


# ---------------------------------------------------------------------------
# ConfirmPopup — yes/no dialog
# ---------------------------------------------------------------------------


class ConfirmPopup:
    """
    Blocking yes/no dialog.
    Returns True (yes) or False (no / cancelled).
    """

    def __init__(self, title: str, message: str) -> None:
        self.title = title
        self.message = message
        self._choice: bool = False
        self._focus_yes = True  # Tab toggles focus

    def run(self) -> bool:
        kb = KeyBindings()

        @kb.add("left")
        @kb.add("right")
        @kb.add("tab")
        @kb.add("shift+tab")
        def _toggle(event: Any) -> None:
            self._focus_yes = not self._focus_yes

        @kb.add("enter")
        @kb.add("y")
        def _yes_or_enter(event: Any) -> None:
            if event.key_sequence[0].key == "y" or self._focus_yes:
                self._choice = True
            event.app.exit()

        @kb.add("n")
        def _no(event: Any) -> None:
            self._choice = False
            event.app.exit()

        @kb.add("escape")
        @kb.add("c-c")
        def _cancel(event: Any) -> None:
            self._choice = False
            event.app.exit()

        def _buttons_text() -> List[tuple[str, str]]:
            yes_style = "class:btn.focused" if self._focus_yes else "class:btn.yes"
            no_style = "class:btn.focused" if not self._focus_yes else "class:btn.no"
            return [
                (yes_style, "  Yes  "),
                ("", "   "),
                (no_style, "  No  "),
            ]

        body = HSplit(
            [
                Window(
                    content=FormattedTextControl(
                        text=lambda: [("class:alert-text", f"  {self.message}  ")]
                    ),
                    height=2,
                ),
                Window(
                    content=FormattedTextControl(text=_buttons_text, focusable=True),
                    height=1,
                ),
                Window(
                    content=FormattedTextControl(
                        text=lambda: [
                            ("class:hint-key", "  ←→/Tab"),
                            ("class:hint-label", " toggle  "),
                            ("class:hint-key", "Enter"),
                            ("class:hint-label", " confirm  "),
                        ]
                    ),
                    height=1,
                ),
            ]
        )

        dialog = Frame(body=body, title=self.title, style="class:frame.border")
        root = FloatContainer(
            content=Window(style="class:popup-backdrop"),
            floats=[Float(content=dialog, xcursor=False, ycursor=False)],
        )
        app: Application[None] = Application(
            layout=Layout(root),
            key_bindings=kb,
            style=POPUP_STYLE,
            full_screen=True,
        )
        app.run()
        return self._choice


# ---------------------------------------------------------------------------
# AlertPopup — informational message
# ---------------------------------------------------------------------------


class AlertPopup:
    """Non-interactive message popup dismissed with Enter/Esc."""

    def __init__(self, title: str, message: str) -> None:
        self.title = title
        self.message = message

    def run(self) -> None:
        kb = KeyBindings()

        @kb.add("enter")
        @kb.add("escape")
        @kb.add("c-c")
        @kb.add("space")
        def _close(event: Any) -> None:
            event.app.exit()

        lines = self.message.splitlines()
        content_lines = [
            Window(
                content=FormattedTextControl(
                    text=lambda ln=ln: [("class:alert-text", f"  {ln}")]
                ),
                height=1,
            )
            for ln in lines
        ]
        hint = Window(
            content=FormattedTextControl(
                text=lambda: [
                    ("class:hint-key", "  Enter/Esc"),
                    ("class:hint-label", " dismiss"),
                ]
            ),
            height=1,
        )
        body = HSplit([*content_lines, Window(height=1), hint])
        dialog = Frame(body=body, title=self.title, style="class:frame.border")
        root = FloatContainer(
            content=Window(style="class:popup-backdrop"),
            floats=[Float(content=dialog, xcursor=False, ycursor=False)],
        )
        app: Application[None] = Application(
            layout=Layout(root),
            key_bindings=kb,
            style=POPUP_STYLE,
            full_screen=True,
        )
        app.run()


# ---------------------------------------------------------------------------
# InputPopup — single freeform text input
# ---------------------------------------------------------------------------


class InputPopup:
    """
    Floating single-line input dialog.
    Returns the entered string, or None if cancelled.
    """

    def __init__(self, title: str, placeholder: str = "") -> None:
        self.title = title
        self.placeholder = placeholder
        self._result: Optional[str] = None

    def run(self) -> Optional[str]:
        text_area = TextArea(
            multiline=False,
            style="class:search-input",
            focus_on_click=True,
        )
        kb = KeyBindings()

        @kb.add("enter")
        def _submit(event: Any) -> None:
            self._result = text_area.text.strip() or None
            event.app.exit()

        @kb.add("escape")
        @kb.add("c-c")
        def _cancel(event: Any) -> None:
            self._result = None
            event.app.exit()

        hint = Window(
            content=FormattedTextControl(
                text=lambda: [
                    ("class:hint-key", "  Enter"),
                    ("class:hint-label", " submit  "),
                    ("class:hint-key", "Esc"),
                    ("class:hint-label", " cancel  "),
                ]
            ),
            height=1,
        )
        body = Frame(
            body=HSplit([Box(body=text_area, padding=1), hint]),
            title=self.title,
            style="class:frame.border",
        )
        root = FloatContainer(
            content=Window(style="class:popup-backdrop"),
            floats=[Float(content=body, xcursor=False, ycursor=False)],
        )
        app: Application[None] = Application(
            layout=Layout(root, focused_element=text_area),
            key_bindings=kb,
            style=POPUP_STYLE,
            full_screen=True,
        )
        app.run()
        return self._result


# ---------------------------------------------------------------------------
# Convenience builders
# ---------------------------------------------------------------------------


def model_select_popup(
    current_model: str,
    extra_options: Optional[Iterable[SelectOption[str]]] = None,
) -> Optional[str]:
    """
    Open the model-switcher popup pre-populated with free/common presets.
    Returns selected model string or None if cancelled.
    """
    presets: List[SelectOption[str]] = [
        SelectOption("openrouter/auto", "openrouter/auto", "Smart routing — picks best free model", "OpenRouter"),
        SelectOption("openrouter/free", "openrouter/free", "Free tier fallback", "OpenRouter"),
        SelectOption("kimi-k2.5-free", "kimi-k2.5-free", "Kimi K2.5 via opencode gateway", "Free / OpenCode"),
        SelectOption("kilocode/kilo-auto/balanced", "kilocode/kilo-auto/balanced", "KiloCode balanced routing", "Free / KiloCode"),
        SelectOption("kilocode/kilo-auto/quality", "kilocode/kilo-auto/quality", "KiloCode quality routing", "Free / KiloCode"),
        SelectOption("gemini-2.5-flash", "gemini-2.5-flash", "Google Gemini 2.5 Flash (needs GEMINI_API_KEY)", "Gemini"),
        SelectOption("gemini-2.5-pro", "gemini-2.5-pro", "Google Gemini 2.5 Pro (needs GEMINI_API_KEY)", "Gemini"),
        SelectOption("gpt-4o", "gpt-4o", "OpenAI GPT-4o (needs OPENAI_API_KEY)", "OpenAI"),
        SelectOption("gpt-4o-mini", "gpt-4o-mini", "OpenAI GPT-4o mini (needs OPENAI_API_KEY)", "OpenAI"),
        SelectOption("llama-3.3-70b-versatile", "llama-3.3-70b-versatile", "Llama 3.3 70B via Groq (needs GROQ_API_KEY)", "Groq"),
        SelectOption("llama-3.1-8b-instant", "llama-3.1-8b-instant", "Llama 3.1 8B Instant via Groq (needs GROQ_API_KEY)", "Groq"),
    ]
    if extra_options:
        presets.extend(extra_options)

    popup = SelectPopup(
        title="Switch Model",
        options=presets,
        current=current_model,
        placeholder="Search models…",
    )
    return popup.run()
