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
import json
from pathlib import Path
import time
from typing import Any, Callable, Dict, Generic, Iterable, List, Optional, TypeVar
import urllib.request

from prompt_toolkit import Application
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from prompt_toolkit.layout import (
    Float,
    FloatContainer,
    HSplit,
    Layout,
    Window,
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Box, Frame, TextArea

T = TypeVar("T")


def _run_app_safely(app: Application[Any]) -> None:
    """Run a prompt_toolkit Application safely, even if an event loop is active."""
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures

        def _runner() -> None:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                new_loop.run_until_complete(app.run_async())
            finally:
                new_loop.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(_runner).result()
    else:
        app.run()


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
        # MCP server manager
        "status-enabled": "#89b482 bold",
        "status-disabled": "#7c6f64",
        "server-name": "#d4be98 bold",
        "server-desc": "#a89984",
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
                else (
                    "class:select-item.current" if is_current else "class:select-item"
                )
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

        list_control = FormattedTextControl(text=self._build_list_text, focusable=False)

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
        _run_app_safely(app)
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
        _run_app_safely(app)
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
        _run_app_safely(app)


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
        _run_app_safely(app)
        return self._result


# ---------------------------------------------------------------------------
# Convenience builders
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# MCP Server Manager Popup (OpenCode-styled toggle dialog)
# ---------------------------------------------------------------------------


class McpPopup:
    """OpenCode-styled interactive MCP server manager.

    Displays all configured MCP servers with status indicators:
      ✓ Enabled  hela-mitosis     (local node)
      ○ Disabled hela-cytosol     (local node)
    Keys:
      ↑ / ↓ / k / j: move selection
      Space / Enter: toggle Enabled/Disabled state in-place
      Esc / q / Ctrl+C: close dialog
    Returns True if any server was toggled, False otherwise.
    """

    def __init__(self, title: str = "MCP Servers") -> None:
        from src.mcp import get_all_mcp_servers_config

        self.title = title
        raw_specs = get_all_mcp_servers_config()
        self._servers: List[Dict[str, Any]] = [
            {"name": name, "enabled": spec.get("enabled", True), "spec": spec}
            for name, spec in sorted(raw_specs.items())
        ]
        self._cursor = 0
        self._has_changed = False

    def _move(self, delta: int) -> None:
        if not self._servers:
            return
        self._cursor = (self._cursor + delta) % len(self._servers)

    def _toggle_current(self) -> None:
        if not self._servers:
            return
        from src.mcp import toggle_mcp_server

        server = self._servers[self._cursor]
        new_state = toggle_mcp_server(server["name"])
        server["enabled"] = new_state
        self._has_changed = True

    def _build_text(self) -> List[tuple[str, str]]:
        if not self._servers:
            return [
                (
                    "class:hint-label",
                    "  No MCP servers configured in ~/.config/frea/mcp.json\n",
                )
            ]

        tokens: List[tuple[str, str]] = []
        for i, server in enumerate(self._servers):
            is_focused = i == self._cursor
            enabled = server["enabled"]

            status_style = (
                "class:status-enabled" if enabled else "class:status-disabled"
            )
            status_text = "  ✓ Enabled " if enabled else "  ○ Disabled"

            name_style = (
                "class:select-item.focused" if is_focused else "class:server-name"
            )
            name_text = f"  {server['name']:<18}"

            raw_cmd = server["spec"].get("command", "")
            if isinstance(raw_cmd, list):
                cmd_summary = Path(raw_cmd[-1]).stem if raw_cmd else "local"
            else:
                cmd_summary = Path(str(raw_cmd)).stem or "local"

            tokens.append((status_style, status_text))
            tokens.append((name_style, name_text))
            tokens.append(("class:hint-label", f" ({cmd_summary})\n"))

        return tokens

    def run(self) -> bool:
        """Run interactive MCP manager. Returns True if any toggles occurred."""
        list_control = FormattedTextControl(
            text=self._build_text,
            focusable=True,
        )

        kb = KeyBindings()

        @kb.add("up")
        @kb.add("k")
        @kb.add("c-p")
        def _up(event: Any) -> None:
            self._move(-1)
            list_control.text = self._build_text  # type: ignore[assignment]

        @kb.add("down")
        @kb.add("j")
        @kb.add("c-n")
        def _down(event: Any) -> None:
            self._move(1)
            list_control.text = self._build_text  # type: ignore[assignment]

        @kb.add("space")
        @kb.add("enter")
        def _toggle(event: Any) -> None:
            self._toggle_current()
            list_control.text = self._build_text  # type: ignore[assignment]

        @kb.add("escape")
        @kb.add("q")
        @kb.add("c-c")
        def _close(event: Any) -> None:
            event.app.exit()

        title_bar = Window(
            content=FormattedTextControl(
                text=lambda: [("class:frame.label", f"  {self.title}  ")]
            ),
            height=1,
            style="class:frame.label",
        )
        sep = Window(height=1, char="─", style="class:frame.border")
        list_win = Window(
            content=list_control,
            height=max(6, min(len(self._servers) + 2, 16)),
        )
        hint_win = Window(
            content=FormattedTextControl(
                text=lambda: [
                    ("class:hint-key", "  ↑↓/j/k"),
                    ("class:hint-label", " navigate  "),
                    ("class:hint-key", "Space/Enter"),
                    ("class:hint-label", " toggle  "),
                    ("class:hint-key", "Esc/q"),
                    ("class:hint-label", " done  "),
                ]
            ),
            height=1,
        )

        dialog = Frame(
            body=HSplit([title_bar, sep, list_win, hint_win]),
            style="class:frame.border",
        )
        root = FloatContainer(
            content=Window(style="class:popup-backdrop"),
            floats=[Float(content=dialog, xcursor=False, ycursor=False)],
        )

        app: Application[None] = Application(
            layout=Layout(root, focused_element=list_win),
            key_bindings=kb,
            style=POPUP_STYLE,
            mouse_support=True,
            full_screen=True,
        )
        _run_app_safely(app)
        return self._has_changed


def mcp_popup() -> bool:
    """Open the MCP server toggle dialog. Returns True if any server was toggled."""
    return McpPopup().run()


# ---------------------------------------------------------------------------
# Dynamic Model Discovery & Model Selector
# ---------------------------------------------------------------------------


def fetch_gateway_models() -> List[SelectOption[str]]:
    """Discover available models from OpenCode Zen and KiloCode gateways.

    Uses local cache with 6-hour TTL to ensure zero latency on subsequent calls.
    """
    cache_path = Path.home() / ".config" / "frea" / "models_cache.json"
    if cache_path.exists():
        try:
            mtime = cache_path.stat().st_mtime
            if (time.time() - mtime) < 6 * 3600:
                raw_data = json.loads(cache_path.read_text(encoding="utf-8"))
                if raw_data:
                    return [
                        SelectOption(
                            label=item["label"],
                            value=item["value"],
                            description=item.get("description", ""),
                            category=item.get("category", ""),
                        )
                        for item in raw_data
                    ]
        except Exception:
            pass

    options: List[SelectOption[str]] = []
    seen_ids = set()

    # Curated top free models (tested and reliable)
    top_free = [
        SelectOption(
            "kilo-auto/free",
            "kilo-auto/free",
            "Free · KiloCode smart free auto router",
            "Free (no key)",
        ),
        SelectOption(
            "nemotron-3.5-lightning-free",
            "nemotron-3.5-lightning-free",
            "Free · OpenCode Zen fast reasoning",
            "Free (no key)",
        ),
        SelectOption(
            "mimo-v2.5-free",
            "mimo-v2.5-free",
            "Free · OpenCode Zen reasoning model",
            "Free (no key)",
        ),
        SelectOption(
            "deepseek-v4-flash-free",
            "deepseek-v4-flash-free",
            "Free · OpenCode Zen",
            "Free (no key)",
        ),
        SelectOption(
            "stepfun/step-3.7-flash:free",
            "stepfun/step-3.7-flash:free",
            "Free · KiloCode Gateway",
            "Free (no key)",
        ),
    ]
    for opt in top_free:
        options.append(opt)
        seen_ids.add(opt.value)

    # 1. Fetch OpenCode Zen models
    try:
        req = urllib.request.Request(
            "https://opencode.ai/zen/v1/models",
            headers={
                "Authorization": "Bearer public",
                "User-Agent": "opencode/1.0.0",
            },
        )
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            data = json.loads(resp.read().decode())
            for m in data.get("data", []):
                mid = m.get("id")
                if not mid or mid in seen_ids:
                    continue
                seen_ids.add(mid)
                is_free = mid.endswith("-free")
                # Filter out models with known upstream server errors (500/503)
                if is_free and any(
                    err in mid
                    for err in (
                        "muse-spark",
                        "ling-3.0-flash-fin",
                        "deepseek-v4-flash-free",
                    )
                ):
                    continue
                cat = "Free (no key)" if is_free else "OpenCode Zen"
                desc = "Free · OpenCode Zen" if is_free else "OpenCode Zen gateway"
                options.append(SelectOption(mid, mid, desc, cat))
    except Exception:
        pass

    # 2. Fetch KiloCode Gateway models
    try:
        req = urllib.request.Request(
            "https://api.kilo.ai/api/gateway/models",
            headers={
                "Authorization": "Bearer public",
                "User-Agent": "opencode/1.0.0",
                "HTTP-Referer": "https://opencode.ai/",
                "X-Title": "opencode",
            },
        )
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            data = json.loads(resp.read().decode())
            for m in data.get("data", []):
                mid = m.get("id")
                if not mid or mid in seen_ids:
                    continue
                seen_ids.add(mid)
                is_free = (
                    ":free" in mid or "/free" in mid or mid.startswith("kilo-auto/free")
                )
                cat = "Free (no key)" if is_free else "KiloCode Gateway"
                desc = "Free · KiloCode gateway" if is_free else "KiloCode gateway"
                options.append(SelectOption(mid, mid, desc, cat))
    except Exception:
        pass

    # 3. Standard external provider presets
    standard_presets = [
        SelectOption(
            "openrouter/auto",
            "openrouter/auto",
            "Smart routing — needs OPENROUTER_API_KEY",
            "OpenRouter",
        ),
        SelectOption(
            "openrouter/free",
            "openrouter/free",
            "Free tier fallback — needs OPENROUTER_API_KEY",
            "OpenRouter",
        ),
        SelectOption(
            "gemini-2.5-flash",
            "gemini-2.5-flash",
            "Google Gemini 2.5 Flash — needs GEMINI_API_KEY",
            "Gemini",
        ),
        SelectOption(
            "gemini-2.5-pro",
            "gemini-2.5-pro",
            "Google Gemini 2.5 Pro — needs GEMINI_API_KEY",
            "Gemini",
        ),
        SelectOption(
            "gpt-4o", "gpt-4o", "OpenAI GPT-4o — needs OPENAI_API_KEY", "OpenAI"
        ),
        SelectOption(
            "gpt-4o-mini",
            "gpt-4o-mini",
            "OpenAI GPT-4o mini — needs OPENAI_API_KEY",
            "OpenAI",
        ),
        SelectOption(
            "llama-3.3-70b-versatile",
            "llama-3.3-70b-versatile",
            "Llama 3.3 70B via Groq — needs GROQ_API_KEY",
            "Groq",
        ),
    ]
    for opt in standard_presets:
        if opt.value not in seen_ids:
            options.append(opt)
            seen_ids.add(opt.value)

    # Cache results
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_data = [
            {
                "label": o.label,
                "value": o.value,
                "description": o.description,
                "category": o.category,
            }
            for o in options
        ]
        cache_path.write_text(json.dumps(cache_data), encoding="utf-8")
    except Exception:
        pass

    return options


def model_select_popup(
    current_model: str,
    extra_options: Optional[Iterable[SelectOption[str]]] = None,
) -> Optional[str]:
    """Open the model-switcher popup populated with dynamic gateway models and presets.

    Returns selected model string or None if cancelled.
    """
    options = fetch_gateway_models()
    if extra_options:
        options.extend(extra_options)

    popup = SelectPopup(
        title="Switch Model",
        options=options,
        current=current_model,
        placeholder="Search models…",
    )
    return popup.run()
