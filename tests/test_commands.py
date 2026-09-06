from src.commands import (
    CommandResult,
    SessionState,
    handle_slash_command,
)


def test_handle_slash_command_help():
    session = SessionState(current_model="gemini-2.5-flash")
    res = handle_slash_command("/help", session)
    assert isinstance(res, CommandResult)
    assert res.handled is True
    assert "Available commands:" in res.output
    assert "/model" in res.output


def test_handle_slash_command_model():
    session = SessionState(current_model="gemini-2.5-flash")
    # Query current model
    res1 = handle_slash_command("/model", session)
    assert res1.handled is True
    assert "gemini-2.5-flash" in res1.output

    # Switch model
    res2 = handle_slash_command("/model gpt-4o", session)
    assert res2.handled is True
    assert session.current_model == "gpt-4o"
    assert "Switched model" in res2.output


def test_handle_slash_command_exit():
    session = SessionState()
    res = handle_slash_command("/exit", session)
    assert res.handled is True
    assert res.exit_requested is True


def test_handle_slash_command_non_command():
    session = SessionState()
    res = handle_slash_command("regular user query", session)
    assert res.handled is False


def test_session_state_history():
    session = SessionState()
    session.record_turn(user="hello", assistant="hi there")
    assert len(session.history) == 2
    assert session.history[0]["content"] == "hello"
    assert session.history[1]["content"] == "hi there"


def test_handle_slash_command_mcp():
    session = SessionState()
    res = handle_slash_command("/mcp", session)
    assert res.handled is True
    assert "MCP" in res.output


def test_handle_slash_command_skills():
    session = SessionState()
    res = handle_slash_command("/skills", session)
    assert res.handled is True
    assert "Skills" in res.output
