from prompt_toolkit.document import Document
from src.commands import SessionState
from src.tui import OpenCodeREPL, OpenCodeTUI, SlashCommandCompleter


def test_command_completer():
    completer = SlashCommandCompleter()
    doc = Document("/m", cursor_position=2)
    completions = list(completer.get_completions(doc, None))
    texts = [c.text for c in completions]
    assert "/model" in texts

    doc_all = Document("/", cursor_position=1)
    all_completions = [c.text for c in completer.get_completions(doc_all, None)]
    for cmd in [
        "/help",
        "/model",
        "/status",
        "/compact",
        "/collapse",
        "/expand",
        "/clear",
        "/exit",
    ]:
        assert cmd in all_completions


def test_status_command():
    state = SessionState(current_model="openrouter/auto", current_provider="openrouter")
    repl = OpenCodeREPL(agent=None, session_state=state)
    status_text = repl.get_status_display()
    assert "openrouter/auto" in status_text
    assert "openrouter" in status_text


def test_opencode_repl_prompt_symbol():
    state = SessionState()
    repl = OpenCodeREPL(agent=None, session_state=state)
    prompt = repl.get_prompt_tokens()
    # Prompt should have OpenCode '❯ ' symbol
    assert any("❯" in token[1] for token in prompt)


def test_opencode_repl_attaches_tool_callbacks():
    from unittest.mock import MagicMock
    from src.agent import AgentLoop

    agent_mock = MagicMock(spec=AgentLoop)
    agent_mock.on_tool_call = None
    agent_mock.on_tool_result = None

    repl = OpenCodeREPL(agent_loop=agent_mock)
    assert agent_mock.on_tool_call is not None
    assert agent_mock.on_tool_result is not None
    tools_cnt, mcp_cnt = repl.get_stats()
    assert tools_cnt >= 0
    assert mcp_cnt >= 0


def test_frea_ascii_logo_spelling():
    from src.ui import LOGO_LEFT, LOGO_RIGHT, clean_glyph_line

    l1 = clean_glyph_line(LOGO_LEFT[1]) + clean_glyph_line(LOGO_RIGHT[1])
    l2 = clean_glyph_line(LOGO_LEFT[2]) + clean_glyph_line(LOGO_RIGHT[2])
    l3 = clean_glyph_line(LOGO_LEFT[3]) + clean_glyph_line(LOGO_RIGHT[3])

    # Line 1: F R E A tops
    assert l1 == "█▀▀▀ █▀▀█ █▀▀▀ █▀▀█"
    # Line 2: F R E A middles (R has diagonal leg █▄▄▀, E has middle bar █▀▀)
    assert l2 == "█▀▀  █▄▄▀ █▀▀  █▀▀█"
    # Line 3: F R E A bottoms (E has bottom bar ▀▀▀▀, R and A have split legs ▀  ▀)
    assert l3 == "▀    ▀  ▀ ▀▀▀▀ ▀  ▀"


def test_repl_status_tracking():
    from unittest.mock import MagicMock
    from src.agent import AgentLoop

    agent_mock = MagicMock(spec=AgentLoop)
    repl = OpenCodeREPL(agent_loop=agent_mock)

    mock_status = MagicMock()
    repl._current_status = mock_status

    repl._on_tool_call("read_file", {"path": "test.txt"})
    mock_status.update.assert_called_with("[bold #5c9cf5]Running[/] [dim]read_file…[/]")

    repl._on_tool_result("read_file", {"path": "test.txt"}, "content")
    assert "Processing response…" in mock_status.update.call_args[0][0]


def test_repl_key_binding_ctrl_o_toggles_fold():
    from unittest.mock import MagicMock

    state = SessionState(current_model="openrouter/auto")
    state.last_response = "line 1\nline 2"
    repl = OpenCodeREPL(session_state=state)
    kb = repl._build_key_bindings()

    bindings = [
        b
        for b in kb.bindings
        if any(getattr(k, "value", str(k)) == "c-o" for k in b.keys)
    ]
    assert len(bindings) == 1
    binding = bindings[0]

    mock_event = MagicMock()
    binding.handler(mock_event)
    assert state.response_collapsed is True
    mock_event.app.invalidate.assert_called_once()

    mock_event.reset_mock()
    binding.handler(mock_event)
    assert state.response_collapsed is False
    mock_event.app.invalidate.assert_called_once()


def test_repl_handle_input_renders_response_card():
    from unittest.mock import MagicMock
    from src.agent import AgentLoop, AgentRunResult

    agent_mock = MagicMock(spec=AgentLoop)
    agent_mock.run.return_value = AgentRunResult(
        final_answer="Line A\nLine B\nLine C\nLine D\nLine E\nLine F",
        steps_taken=1,
        tool_calls_count=0,
        success=True,
    )
    state = SessionState(current_model="openrouter/auto")
    repl = OpenCodeREPL(agent_loop=agent_mock, session=state)

    should_exit, output = repl.handle_input("hello")
    assert should_exit is False
    assert "Assistant" in output
    assert "▼ Collapse · Ctrl+O / /collapse" in output
    assert "Line A" in output
    assert state.last_response == "Line A\nLine B\nLine C\nLine D\nLine E\nLine F"

    state.response_collapsed = True
    should_exit, output_collapsed = repl.handle_input("hello again")
    assert "▶ Expand (+4 lines) · Ctrl+O / /expand" in output_collapsed
    assert "… 4 more line(s) · ctrl+o or /expand" in output_collapsed


def test_opencode_tui_in_place_fold_and_expand():
    state = SessionState(current_model="openrouter/auto")
    repl = OpenCodeREPL(session_state=state)
    tui = OpenCodeTUI(repl)

    # Empty initial state
    assert len(tui.cards) == 0
    assert tui.collapse_last() is False
    assert tui.expand_last() is False

    # Add card with 5 lines
    card = tui.add_card(
        kind="assistant",
        title="Assistant",
        body="Line 1\nLine 2\nLine 3\nLine 4\nLine 5",
    )
    assert len(tui.cards) == 1
    assert card.collapsed is False
    assert card.is_foldable() is True

    # Collapse in-place
    assert tui.collapse_last() is True
    assert card.collapsed is True
    assert len(tui.cards) == 1  # No duplicate card added

    # Expand in-place
    assert tui.expand_last() is True
    assert card.collapsed is False
    assert len(tui.cards) == 1

    # Toggle in-place
    assert tui.toggle_last_foldable() is True
    assert card.collapsed is True
    assert len(tui.cards) == 1

    assert tui.toggle_last_foldable() is True
    assert card.collapsed is False
    assert len(tui.cards) == 1


def test_opencode_tui_mouse_and_hover():
    from prompt_toolkit.mouse_events import MouseButton, MouseEvent, MouseEventType

    state = SessionState(current_model="openrouter/auto")
    repl = OpenCodeREPL(session_state=state)
    tui = OpenCodeTUI(repl)

    card = tui.add_card(
        kind="assistant",
        title="Assistant",
        body="Line 1\nLine 2\nLine 3\nLine 4",
    )

    tui.set_hovered_card(card.id)
    assert tui.hovered_card_id == card.id

    tokens = tui._get_transcript_tokens()
    # Check that bg color is applied when hovered
    assert any(f"bg:{repl.theme.background_panel}" in tok[0] for tok in tokens)

    # Find token with mouse handler
    tokens_with_handler = [tok for tok in tokens if callable(tok[2])]
    assert len(tokens_with_handler) > 0
    handler = tokens_with_handler[0][2]

    # Click toggles card collapsed state in-place
    click_event = MouseEvent(
        position=(0, 0),
        event_type=MouseEventType.MOUSE_DOWN,
        button=MouseButton.LEFT,
        modifiers=set(),
    )
    handler(click_event)
    assert card.collapsed is True

    # Another click expands it
    handler(click_event)
    assert card.collapsed is False


def test_opencode_tui_non_foldable():
    state = SessionState(current_model="openrouter/auto")
    repl = OpenCodeREPL(session_state=state)
    tui = OpenCodeTUI(repl)

    short_card = tui.add_card(kind="assistant", title="Assistant", body="Single line")
    assert short_card.is_foldable() is False

    user_card = tui.add_card(kind="user", title="You", body="Long\nUser\nPrompt\nLines")
    assert user_card.is_foldable() is False

    assert tui.collapse_last() is False
    assert tui.expand_last() is False
    assert tui.toggle_card(short_card.id) is False
    assert tui.toggle_card(user_card.id) is False
