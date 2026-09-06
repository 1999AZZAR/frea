"""Interactive Terminal User Interface (TUI) REPL for Frea."""

import sys
from typing import Optional, TextIO, Tuple
from src.agent import AgentLoop
from src.commands import SessionState, handle_slash_command


BANNER = """
╭───────────────────────────────────────────────╮
│  Frea - AI Coding Agent & Terminal Harness     │
│  Type your query, or /help for slash commands │
╰───────────────────────────────────────────────╯
"""


class InteractiveREPL:
    """Read-Eval-Print-Loop for interactive Frea sessions."""

    def __init__(
        self,
        agent_loop: AgentLoop,
        session: Optional[SessionState] = None,
    ):
        self.agent_loop = agent_loop
        self.session = session or SessionState()

    def handle_input(self, line: str) -> Tuple[bool, str]:
        """Process a single input line, dispatching to slash commands or agent loop."""
        text = line.strip()
        if not text:
            return False, ""

        if text.startswith("/"):
            res = handle_slash_command(text, self.session)
            return res.exit_requested, res.output or ""

        agent_result = self.agent_loop.run(text)
        self.session.record_turn(text, agent_result.final_answer)
        return False, agent_result.final_answer

    def run_repl(
        self,
        input_stream: Optional[TextIO] = None,
        output_stream: Optional[TextIO] = None,
    ) -> int:
        """Run interactive loop until exit requested or EOF reached."""
        in_stream = input_stream or sys.stdin
        out_stream = output_stream or sys.stdout

        out_stream.write(BANNER)
        out_stream.flush()

        while True:
            try:
                out_stream.write(f"\n[{self.session.current_model}] frea ❯ ")
                out_stream.flush()

                line = in_stream.readline()
                if not line:
                    break

                should_exit, message = self.handle_input(line)
                if message:
                    out_stream.write(f"\n{message}\n")
                    out_stream.flush()

                if should_exit:
                    break
            except (KeyboardInterrupt, EOFError):
                out_stream.write("\nSession interrupted. Exiting.\n")
                out_stream.flush()
                break

        return 0
