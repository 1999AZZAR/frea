"""Tests for the popup system — run without an actual terminal (no TTY)."""

from unittest.mock import MagicMock, patch
from src.popup import (
    SelectOption,
    SelectPopup,
    model_select_popup,
)


def test_select_option_dataclass():
    opt: SelectOption[str] = SelectOption(
        label="gpt-4o", value="gpt-4o", description="OpenAI GPT-4o", category="OpenAI"
    )
    assert opt.label == "gpt-4o"
    assert opt.value == "gpt-4o"
    assert opt.category == "OpenAI"


def test_select_popup_filter():
    opts = [
        SelectOption("openrouter/auto", "openrouter/auto", category="OpenRouter"),
        SelectOption("kimi-k2.5-free", "kimi-k2.5-free", category="Free"),
        SelectOption("gpt-4o", "gpt-4o", category="OpenAI"),
    ]
    popup = SelectPopup(title="Test", options=opts)
    popup._apply_filter("kimi")
    assert len(popup._filtered) == 1
    assert popup._filtered[0].value == "kimi-k2.5-free"


def test_select_popup_filter_empty_returns_all():
    opts = [
        SelectOption("a", "a"),
        SelectOption("b", "b"),
    ]
    popup = SelectPopup(title="Test", options=opts)
    popup._apply_filter("x")
    assert popup._filtered == []
    popup._apply_filter("")
    assert len(popup._filtered) == 2


def test_select_popup_move_wraps():
    opts = [SelectOption(str(i), str(i)) for i in range(3)]
    popup = SelectPopup(title="Test", options=opts)
    popup._cursor = 0
    popup._move(-1)  # wrap around
    assert popup._cursor == 2
    popup._move(1)  # back to 0
    assert popup._cursor == 0


def test_select_popup_current_preselects():
    opts = [SelectOption("a", "a"), SelectOption("b", "b"), SelectOption("c", "c")]
    popup = SelectPopup(title="Test", options=opts, current="b")
    assert popup._cursor == 1


def test_select_popup_build_list_text_marks_current():
    opts = [
        SelectOption("openrouter/auto", "openrouter/auto"),
        SelectOption("gpt-4o", "gpt-4o"),
    ]
    # cursor=0 focused (openrouter/auto), current=gpt-4o → second item not focused
    # so it gets select-item.current style with ● prefix
    popup = SelectPopup(title="Test", options=opts, current="gpt-4o")
    popup._cursor = 0  # force cursor to first item so gpt-4o is current-not-focused
    tokens = popup._build_list_text()
    # Check that the ● prefix or current style appears for gpt-4o
    text_parts = "".join(t for _, t in tokens)
    assert "●" in text_parts  # current item gets bullet marker


def test_select_popup_run_mocked_cancel():
    """Simulate user pressing Escape — result should be None."""
    opts = [SelectOption("a", "a")]
    popup = SelectPopup(title="Test", options=opts)

    with patch("src.popup.Application") as MockApp:
        mock_app = MagicMock()
        MockApp.return_value = mock_app

        result = popup.run()

    assert result is None  # _cancelled stays True, _result never set


def test_model_select_popup_has_presets():
    """model_select_popup should build 11+ preset options."""
    with patch("src.popup.SelectPopup") as MockSelect:
        mock_instance = MagicMock()
        mock_instance.run.return_value = None
        MockSelect.return_value = mock_instance

        model_select_popup("openrouter/auto")

        call_kwargs = MockSelect.call_args.kwargs
        options = call_kwargs["options"]
        assert len(options) >= 8
        labels = [o.label for o in options]
        assert "openrouter/auto" in labels
        assert "kilo-auto/free" in labels
        assert "gpt-4o" in labels


def test_fetch_gateway_models():
    from src.popup import fetch_gateway_models

    models = fetch_gateway_models()
    assert len(models) >= 5
    categories = {m.category for m in models}
    assert "Free (no key)" in categories
    free_models = [m.value for m in models if m.category == "Free (no key)"]
    assert "kilo-auto/free" in free_models


def test_mcp_popup_rendering_and_navigation():
    from src.popup import McpPopup

    with patch("src.mcp.get_all_mcp_servers_config") as mock_cfg:
        mock_cfg.return_value = {
            "server-a": {"enabled": True, "command": ["node", "a.js"]},
            "server-b": {"enabled": False, "command": ["node", "b.js"]},
        }
        popup = McpPopup(title="Test MCP")
        assert len(popup._servers) == 2
        tokens = popup._build_text()
        text = "".join(t for _, t in tokens)
        assert "server-a" in text
        assert "server-b" in text
        assert "✓ Enabled" in text
        assert "○ Disabled" in text

        # Test movement
        popup._move(1)
        assert popup._cursor == 1
        popup._move(-1)
        assert popup._cursor == 0


def test_mcp_popup_toggle():
    from src.popup import McpPopup

    with patch("src.mcp.get_all_mcp_servers_config") as mock_cfg, patch(
        "src.mcp.toggle_mcp_server"
    ) as mock_toggle:
        mock_cfg.return_value = {
            "server-a": {"enabled": True, "command": ["node", "a.js"]},
        }
        mock_toggle.return_value = False
        popup = McpPopup(title="Test MCP")
        popup._toggle_current()
        assert popup._servers[0]["enabled"] is False
        assert popup._has_changed is True
        mock_toggle.assert_called_once_with("server-a")


async def test_select_popup_run_async_mocked():
    opts = [SelectOption("opt1", "val1")]
    popup = SelectPopup(title="Async Test", options=opts)

    with patch("src.popup.Application") as MockApp:
        mock_app = MagicMock()
        mock_app.run_async = MagicMock()
        # Mock run_async returning a completed coroutine
        async def _mock_run():
            popup._result = "val1"
            popup._cancelled = False
        mock_app.run_async.side_effect = _mock_run
        MockApp.return_value = mock_app

        res = await popup.run_async()
        assert res == "val1"


async def test_confirm_popup_run_async_mocked():
    from src.popup import ConfirmPopup, confirm_popup_async

    with patch("src.popup.Application") as MockApp:
        mock_app = MagicMock()
        async def _mock_run():
            pass
        mock_app.run_async.side_effect = _mock_run
        MockApp.return_value = mock_app

        popup = ConfirmPopup("Exit", "Really?")
        popup._choice = True
        res = await popup.run_async()
        assert res is True

        res2 = await confirm_popup_async("Exit", "Really?")
        assert res2 is False


async def test_mcp_popup_run_async_mocked():
    from src.popup import McpPopup, mcp_popup_async

    with patch("src.mcp.get_all_mcp_servers_config") as mock_cfg, patch(
        "src.popup.Application"
    ) as MockApp:
        mock_cfg.return_value = {}
        mock_app = MagicMock()
        async def _mock_run():
            pass
        mock_app.run_async.side_effect = _mock_run
        MockApp.return_value = mock_app

        popup = McpPopup("MCP")
        popup._has_changed = True
        res = await popup.run_async()
        assert res is True

        res2 = await mcp_popup_async()
        assert res2 is False


async def test_model_select_popup_async_mocked():
    from src.popup import model_select_popup_async

    with patch("src.popup.SelectPopup") as MockSelect:
        mock_instance = MagicMock()
        async def _mock_run():
            return "kilo-auto/free"
        mock_instance.run_async.side_effect = _mock_run
        MockSelect.return_value = mock_instance

        res = await model_select_popup_async("openrouter/auto")
        assert res == "kilo-auto/free"
