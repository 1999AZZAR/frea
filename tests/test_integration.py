from io import StringIO
from unittest.mock import patch
from src.agent import AgentLoop, ModelResponse, ToolCall
from src.commands import SessionState
from src.executor import ToolExecutor
from src.runner import run_cli
from src.tui import InteractiveREPL


class MockE2EProvider:
    def __init__(self, target_path: str = "test_e2e.txt"):
        self.step = 0
        self.target_path = target_path

    def generate(self, messages, tools=None):
        if self.step == 0:
            self.step += 1
            return ModelResponse(
                content="I will write a greeting file.",
                tool_calls=[
                    ToolCall(
                        id="call_e2e_1",
                        name="file_write",
                        arguments={"path": self.target_path, "content": "hello e2e"},
                    )
                ],
            )
        else:
            return ModelResponse(content="E2E test task completed.", tool_calls=[])


def test_e2e_headless_run(tmp_path):
    target_file = str(tmp_path / "test_e2e.txt")
    provider = MockE2EProvider(target_path=target_file)
    executor = ToolExecutor(auto_approve=True)
    agent = AgentLoop(provider=provider, executor=executor)

    output_stream = StringIO()

    def headless_handler(config):
        res = agent.run(config.prompt)
        output_stream.write(res.final_answer)
        return 0

    exit_code = run_cli(
        argv=["-p", "run e2e test", "--yes"],
        headless_handler=headless_handler,
    )
    assert exit_code == 0
    assert "E2E test task completed." in output_stream.getvalue()


def test_e2e_interactive_run():
    provider = MockE2EProvider()
    executor = ToolExecutor(auto_approve=True)
    agent = AgentLoop(provider=provider, executor=executor)
    session = SessionState(current_model="openrouter/auto")
    repl = InteractiveREPL(agent_loop=agent, session=session)

    in_stream = StringIO("/status\n/exit\n")
    out_stream = StringIO()

    exit_code = run_cli(
        argv=[],
        interactive_handler=lambda cfg: repl.run_repl(
            input_stream=in_stream, output_stream=out_stream
        ),
    )
    assert exit_code == 0
    output = out_stream.getvalue()
    assert "openrouter/auto" in output
    assert "Exiting Frea session" in output


def test_e2e_permission_prompt_rendering():
    from src.executor import default_confirm

    with patch("builtins.input", return_value="y"), patch(
        "src.ui.console.print"
    ) as mock_print:
        allowed = default_confirm("bash_run", {"command": "echo test"})
        assert allowed is True
        mock_print.assert_called_once()
        call_args = str(mock_print.call_args)
        assert "Permission" in call_args or "△" in call_args
