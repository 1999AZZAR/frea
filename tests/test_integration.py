from io import StringIO
from src.agent import AgentLoop, ModelResponse, ToolCall
from src.executor import ToolExecutor
from src.runner import run_cli
from src.tui import InteractiveREPL


class MockE2EProvider:
    def __init__(self):
        self.step = 0

    def generate(self, messages, tools=None):
        if self.step == 0:
            self.step += 1
            return ModelResponse(
                content="I will write a greeting file.",
                tool_calls=[
                    ToolCall(
                        id="call_e2e_1",
                        name="file_write",
                        arguments={"path": "test_e2e.txt", "content": "hello e2e"},
                    )
                ],
            )
        else:
            return ModelResponse(content="E2E test task completed.", tool_calls=[])


def test_e2e_headless_run(tmp_path):
    provider = MockE2EProvider()
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
    repl = InteractiveREPL(agent_loop=agent)

    in_stream = StringIO("/exit\n")
    out_stream = StringIO()

    exit_code = run_cli(
        argv=[],
        interactive_handler=lambda cfg: repl.run_repl(
            input_stream=in_stream, output_stream=out_stream
        ),
    )
    assert exit_code == 0
    assert "Exiting Frea session" in out_stream.getvalue()
