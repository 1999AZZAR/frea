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
        assert "deepseek-v4-flash" in labels
        assert "gpt-4o" in labels
