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
