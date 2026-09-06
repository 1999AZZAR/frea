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
    # Query current model – shows preset list
    res1 = handle_slash_command("/model", session)
    assert res1.handled is True
    assert "gemini-2.5-flash" in res1.output
    assert "Presets" in res1.output

    # Switch model with no callback – just updates session
    res2 = handle_slash_command("/model gpt-4o", session)
    assert res2.handled is True
    assert session.current_model == "gpt-4o"
    assert "Switched model" in res2.output

    # Switch model with a working callback
    switched = []
    session.on_model_switch = lambda m: switched.append(m)
    handle_slash_command("/model openrouter/auto", session)
    assert session.current_model == "openrouter/auto"
    assert switched == ["openrouter/auto"]

    # Switch model with a failing callback – should rollback
    def _bad_switch(m):
        raise RuntimeError("API error")

    session.on_model_switch = _bad_switch
    prev = session.current_model
    res_fail = handle_slash_command("/model bad-model", session)
    assert "Failed to switch model" in res_fail.output
    assert session.current_model == prev  # rolled back


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


def test_handle_slash_command_expand_compact_collapse():
    session = SessionState(current_model="openrouter/auto")
    # Empty last response
    res_collapse_empty = handle_slash_command("/collapse", session)
    assert res_collapse_empty.handled is True
    assert session.response_collapsed is True
    assert "Collapsed mode enabled" in res_collapse_empty.output

    res_exp_empty = handle_slash_command("/expand", session)
    assert res_exp_empty.handled is True
    assert session.response_collapsed is False
    assert "Expanded mode enabled" in res_exp_empty.output

    # With last response
    session.last_response = "\n".join([f"Output line {i}" for i in range(10)])

    res_collapse = handle_slash_command("/collapse", session)
    assert res_collapse.handled is True
    assert session.response_collapsed is True
    assert "▶ Expand" in res_collapse.output
    assert "more line(s)" in res_collapse.output

    res_expand = handle_slash_command("/expand", session)
    assert res_expand.handled is True
    assert session.response_collapsed is False
    assert "▼ Collapse" in res_expand.output
    assert "Output line 9" in res_expand.output

    # /compact compresses conversation history
    for i in range(15):
        session.record_turn(f"user {i}", f"assistant {i}")
    res_compact = handle_slash_command("/compact", session)
    assert res_compact.handled is True
    assert "Compacted history from" in res_compact.output
