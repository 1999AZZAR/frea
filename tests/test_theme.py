from src.ui import Theme, render_header, render_logo, render_statusline


def test_opencode_theme_palette():
    theme = Theme()
    assert theme.primary == "#fab283"
    assert theme.secondary == "#5c9cf5"
    assert theme.accent == "#9d7cd8"
    assert theme.error == "#e06c75"
    assert theme.warning == "#f5a742"
    assert theme.success == "#7fd88f"
    assert theme.info == "#56b6c2"
    assert theme.text == "#eeeeee"
    assert theme.text_muted == "#808080"


def test_render_block_logo():
    logo_lines = render_logo(raw=True)
    assert len(logo_lines) == 4
    # Check that block characters are present
    assert any("█" in line for line in logo_lines)


def test_render_session_header():
    header = render_header("openrouter/auto", "/home/user/project", tools_count=6)
    assert "openrouter/auto" in header
    assert "project" in header
    assert "6 tools" in header.lower() or "6" in header


def test_render_statusline():
    status = render_statusline(
        "/home/user/project", "openrouter/auto", tools_count=6, width=80
    )
    assert "project" in status
    assert "openrouter/auto" in status
    assert "6" in status
    assert "/status" in status


def test_tint_color():
    from src.ui import tint

    # Tinting black (#000000) with white (#ffffff) at 0.5 should be gray (#808080)
    t = tint("#000000", "#ffffff", 0.5)
    assert t == "#808080"


def test_render_logo_rich_text():
    from src.ui import render_logo
    from rich.text import Text

    text = render_logo(raw=False)
    assert isinstance(text, Text)
    assert len(text.plain) > 0
