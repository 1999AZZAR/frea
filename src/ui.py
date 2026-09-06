"""OpenCode 1:1 Theme, Typography, and UI Rendering Components for Frea."""

from dataclasses import dataclass
import os
import shutil
from typing import List, Tuple, Union
from rich.console import Console
from rich.text import Text


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Parse hex color string (#rrggbb or #rgb) to RGB integer tuple."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Format RGB integer tuple to hex color string."""
    return (
        f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"
    )


def tint(base_hex: str, overlay_hex: str, alpha: float) -> str:
    """Tint base color by overlay color with factor alpha (matches OpenCode tint)."""
    br, bg, bb = hex_to_rgb(base_hex)
    or_, og, ob = hex_to_rgb(overlay_hex)
    r = round(br + (or_ - br) * alpha)
    g = round(bg + (og - bg) * alpha)
    b = round(bb + (ob - bb) * alpha)
    return rgb_to_hex(r, g, b)


@dataclass(frozen=True)
class Theme:
    """Semantic color theme mirroring opencode.json."""

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
    background_element: str = "#1e1e1e"
    border: str = "#484848"
    border_active: str = "#606060"
    border_subtle: str = "#3c3c3c"
    diff_added: str = "#4fd6be"
    diff_removed: str = "#c53b53"
    diff_context: str = "#828bb8"
    diff_highlight_added: str = "#b8db87"
    diff_highlight_removed: str = "#e26a75"
    diff_added_bg: str = "#20303b"
    diff_removed_bg: str = "#37222c"
    diff_context_bg: str = "#141414"
    diff_line_number: str = "#8f8f8f"


THEME = Theme()
console = Console(highlight=False)

LOGO_MARKS = "_^~,"

LOGO_LEFT = [
    "         ",
    "█▀▀▀ █▀▀█",
    "█^^  █▄▄▀",
    "▀    ▀  ▀",
]

LOGO_RIGHT = [
    "          ",
    " █▀▀▀ █▀▀█",
    " █^^  █^^█",
    " ▀▀▀▀ ▀  ▀",
]


def clean_glyph_line(line: str) -> str:
    """Convert OpenCode glyph marks into plain Unicode block representation."""
    res = []
    for ch in line:
        if ch == "_":
            res.append(" ")
        elif ch in ("^", "~"):
            res.append("▀")
        elif ch == ",":
            res.append("▄")
        else:
            res.append(ch)
    return "".join(res)


def render_line_glyphs(
    line: str,
    fg_hex: str,
    bg_hex: str,
    bold: bool = False,
) -> Text:
    """Render a logo line applying OpenCode shaded glyph background rendering."""
    shadow_hex = tint(bg_hex, fg_hex, 0.25)
    out = Text()
    for char in line:
        if char == "_":
            out.append(" ", style=f"on {shadow_hex}")
        elif char == "^":
            out.append("▀", style=f"{fg_hex} on {shadow_hex}")
        elif char == "~":
            out.append("▀", style=f"{shadow_hex}")
        elif char == ",":
            out.append("▄", style=f"{shadow_hex}")
        else:
            style = f"bold {fg_hex}" if bold else fg_hex
            out.append(char, style=style)
    return out


def format_path(path: str) -> str:
    """Tilde-abbreviate home directory path."""
    home = os.path.expanduser("~")
    if path.startswith(home):
        return "~" + path[len(home) :]
    return path


def render_logo(raw: bool = False, theme: Theme = THEME) -> Union[List[str], Text]:
    """Render FREA block logo matching OpenCode typography and shading."""
    if raw:
        return [
            f"{clean_glyph_line(LOGO_LEFT[i])}{clean_glyph_line(LOGO_RIGHT[i])}"
            for i in range(4)
        ]

    out = Text()
    for i in range(4):
        left_part = render_line_glyphs(
            LOGO_LEFT[i], theme.text_muted, theme.background, bold=False
        )
        right_part = render_line_glyphs(
            LOGO_RIGHT[i], theme.primary, theme.background, bold=True
        )
        out.append_text(left_part)
        out.append_text(right_part)
        out.append("\n")
    return out


def render_header(
    model: str,
    directory: str,
    tools_count: int = 6,
    mcp_count: int = 0,
    version: str = "0.2.0",
    theme: Theme = THEME,
) -> str:
    """Render OpenCode-styled greeting header."""
    cwd_disp = format_path(directory)
    c1 = f"[{theme.text_muted}]"
    c2 = f"[bold {theme.primary}]"
    c_sub = f"[{theme.accent}]"
    c_txt = f"[{theme.text}]"
    c_mut = f"[{theme.text_muted}]"
    c_info = f"[{theme.info}]"
    c_suc = f"[{theme.success}]"
    end = "[/]"

    l1_left = clean_glyph_line(LOGO_LEFT[1])
    l1_right = clean_glyph_line(LOGO_RIGHT[1])
    l2_left = clean_glyph_line(LOGO_LEFT[2])
    l2_right = clean_glyph_line(LOGO_RIGHT[2])
    l3_left = clean_glyph_line(LOGO_LEFT[3])
    l3_right = clean_glyph_line(LOGO_RIGHT[3])

    mcp_info = f" · {c_suc}⊙ {mcp_count} MCP{end}" if mcp_count > 0 else ""

    lines = [
        f"{c1}{l1_left}{end}{c2}{l1_right}{end}   {c_sub}frea v{version}{end}",
        f"{c1}{l2_left}{end}{c2}{l2_right}{end}   {c_txt}Model:{end} {c_info}{model}{end}",
        f"{c1}{l3_left}{end}{c2}{l3_right}{end}   {c_txt}Directory:{end} {c_mut}{cwd_disp}{end} · {c_mut}{tools_count} tools{end}{mcp_info}",
        f"\n{c_mut}Type {end}[bold {theme.accent}]/help{end}{c_mut} for commands, {end}[bold {theme.accent}]/model{end}{c_mut} to switch, {end}[bold {theme.accent}]/status{end}{c_mut} for details, {end}[bold {theme.accent}]/exit{end}{c_mut} to quit.{end}\n",
    ]
    return "\n".join(lines)


def render_statusline(
    directory: str,
    model: str = "",
    tools_count: int = 6,
    mcp_count: int = 0,
    permissions_count: int = 0,
    width: int | None = None,
    theme: Theme = THEME,
) -> str:
    """Render 1:1 OpenCode bottom statusline."""
    if width is None:
        width = shutil.get_terminal_size(fallback=(80, 24)).columns

    left = format_path(directory)
    right_parts = []
    if permissions_count > 0:
        right_parts.append(
            f"△ {permissions_count} Permission{'s' if permissions_count > 1 else ''}"
        )
    if model:
        right_parts.append(f"• {model}")
    right_parts.append(f"• {tools_count} Tools")
    if mcp_count > 0:
        right_parts.append(f"⊙ {mcp_count} MCP")
    right_parts.append("^O: fold")
    right_parts.append("/status")
    right_parts.append("/help")
    right = "   ".join(right_parts)

    spacing = max(2, width - len(left) - len(right))
    return f"{left}{' ' * spacing}{right}"
