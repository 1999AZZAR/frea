from io import StringIO
from unittest.mock import MagicMock
from src.agent import AgentLoop, AgentRunResult
from src.commands import SessionState
from src.tui import InteractiveREPL


def test_tui_handles_slash_command():
    agent_mock = MagicMock(spec=AgentLoop)
    session = SessionState(current_model="gemini-2.5-flash")
    repl = InteractiveREPL(agent_loop=agent_mock, session=session)

    should_exit, output = repl.handle_input("/model")
    assert should_exit is False
    assert "gemini-2.5-flash" in output
    agent_mock.run.assert_not_called()


def test_tui_handles_exit_command():
    agent_mock = MagicMock(spec=AgentLoop)
    session = SessionState()
    repl = InteractiveREPL(agent_loop=agent_mock, session=session)

    should_exit, output = repl.handle_input("/exit")
    assert should_exit is True
    assert "Exiting" in output
    agent_mock.run.assert_not_called()


def test_tui_runs_agent_on_query():
    agent_mock = MagicMock(spec=AgentLoop)
    agent_mock.run.return_value = AgentRunResult(
        final_answer="Code refactored successfully.",
        steps_taken=2,
        tool_calls_count=1,
        success=True,
    )
    session = SessionState()
    repl = InteractiveREPL(agent_loop=agent_mock, session=session)

    should_exit, output = repl.handle_input("refactor main.py")
    assert should_exit is False
    assert "Code refactored successfully." in output
    agent_mock.run.assert_called_once_with("refactor main.py")
    assert len(session.history) == 2


def test_tui_run_repl_stream():
    agent_mock = MagicMock(spec=AgentLoop)
    agent_mock.run.return_value = AgentRunResult(
        final_answer="Answer to test",
        steps_taken=1,
        tool_calls_count=0,
        success=True,
    )
    session = SessionState()
    repl = InteractiveREPL(agent_loop=agent_mock, session=session)

    input_data = StringIO("test query\n/exit\n")
    output_data = StringIO()

    repl.run_repl(input_stream=input_data, output_stream=output_data)
    rendered = output_data.getvalue()
    assert "Answer to test" in rendered
    assert "Exiting Frea session" in rendered
