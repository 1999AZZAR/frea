from prompt_toolkit.document import Document
from src.commands import SessionState
from src.tui import OpenCodeREPL, SlashCommandCompleter


def test_command_completer():
    completer = SlashCommandCompleter()
    doc = Document("/m", cursor_position=2)
    completions = list(completer.get_completions(doc, None))
    texts = [c.text for c in completions]
    assert "/model" in texts

    doc_all = Document("/", cursor_position=1)
    all_completions = [c.text for c in completer.get_completions(doc_all, None)]
    for cmd in ["/help", "/model", "/status", "/compact", "/clear", "/exit"]:
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
