from dataclasses import dataclass
import os
import shutil
from rich.console import Console
from rich.text import Text


@dataclass(frozen=True)
class Theme:
    primary: str = "#fab283"
    secondary: str = "#5c9cf5"
    accent: str = "#9d7cd8"
    error: str = "#e06c75"
    warning: str = "#f5a742"
    success: str = "#7fd88f"
    info: str = "#56b6c2"
    text: str = "#eeeeee"
    text_muted: str = "#808080"
    background: str = "#0a0a0a"
    background_panel: str = "#141414"
    border: str = "#484848"
    border_subtle: str = "#3c3c3c"
    diff_added: str = "#4fd6be"
    diff_removed: str = "#c53b53"
    diff_added_bg: str = "#20303b"
    diff_removed_bg: str = "#37222c"


THEME = Theme()
console = Console(highlight=False)

LOGO_LEFT = [
    "         ",
    "█▀▀▀ █▀▀█",
    "█▀▀  █▀▀▄",
    "▀    ▀  ▀",
]

LOGO_RIGHT = [
    "         ",
    " █▀▀▀ █▀▀█",
    " █▀▀  █▀▀█",
    " ▀▀▀▀ ▀  ▀",
]


def format_path(path: str) -> str:
    home = os.path.expanduser("~")
    if path.startswith(home):
        return "~" + path[len(home) :]
    return path


def render_logo(raw: bool = False, theme: Theme = THEME) -> list[str] | Text:
    combined = [f"{LOGO_LEFT[i]}{LOGO_RIGHT[i]}" for i in range(4)]
    if raw:
        return combined

    text = Text()
    for i in range(4):
        text.append(LOGO_LEFT[i], style=theme.text_muted)
        text.append(LOGO_RIGHT[i], style=f"bold {theme.primary}")
        text.append("\n")
    return text


def render_header(
    model: str,
    directory: str,
    tools_count: int = 6,
    version: str = "0.2.0",
    theme: Theme = THEME,
) -> str:
    cwd_disp = format_path(directory)
    c1 = f"[{theme.text_muted}]"
    c2 = f"[bold {theme.primary}]"
    c_sub = f"[{theme.accent}]"
    c_txt = f"[{theme.text}]"
    c_mut = f"[{theme.text_muted}]"
    c_info = f"[{theme.info}]"
    end = "[/]"

    lines = [
        f"{c1}{LOGO_LEFT[1]}{end}{c2}{LOGO_RIGHT[1]}{end}   {c_sub}frea v{version}{end} {c_mut}(OpenCode Edition){end}",
        f"{c1}{LOGO_LEFT[2]}{end}{c2}{LOGO_RIGHT[2]}{end}   {c_txt}Model:{end} {c_info}{model}{end}",
        f"{c1}{LOGO_LEFT[3]}{end}{c2}{LOGO_RIGHT[3]}{end}   {c_txt}Directory:{end} {c_mut}{cwd_disp}{end} · {c_mut}{tools_count} tools{end}",
        f"\n{c_mut}Type {end}[bold {theme.accent}]/help{end}{c_mut} for commands, {end}[bold {theme.accent}]/model{end}{c_mut} to switch, {end}[bold {theme.accent}]/exit{end}{c_mut} to quit.{end}\n",
    ]
    return "\n".join(lines)


def render_statusline(
    directory: str,
    model: str,
    tools_count: int = 6,
    permissions_count: int = 0,
    width: int | None = None,
    theme: Theme = THEME,
) -> str:
    if width is None:
        width = shutil.get_terminal_size(fallback=(80, 24)).columns

    left = format_path(directory)
    right_parts = []
    if permissions_count > 0:
        right_parts.append(
            f"△ {permissions_count} Permission{'s' if permissions_count > 1 else ''}"
        )
    right_parts.append(f"• {model}")
    right_parts.append(f"⊙ {tools_count} Tools")
    right_parts.append("/help")
    right = "   ".join(right_parts)

    spacing = max(2, width - len(left) - len(right))
    return f"{left}{' ' * spacing}{right}"
