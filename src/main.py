"""Modernized entrypoint for Frea CLI and interactive TUI harness."""

# ruff: noqa: E402
import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SRC_DIR.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(1, str(_SRC_DIR))

from src.agent import AgentLoop
from src.cli import CLIConfig
from src.commands import SessionState
from src.config import load_frea_config
from src.executor import ToolExecutor
from src.providers import get_provider
from src.runner import run_cli
from src.tui import InteractiveREPL


def headless_run(config: CLIConfig) -> int:
    frea_cfg = load_frea_config(config.config_path)
    model_name = config.model or frea_cfg.get("model") or "kilo-auto/free"
    auto_approve = config.yes or frea_cfg.get("auto_approve", False)

    try:
        provider = get_provider(model_name)
    except Exception:
        provider = get_provider("kilo-auto/free")

    executor = ToolExecutor(auto_approve=auto_approve)
    agent = AgentLoop(provider=provider, executor=executor)
    result = agent.run(config.prompt)
    print(result.final_answer)
    return 0 if result.success else 1


def interactive_run(config: CLIConfig) -> int:
    frea_cfg = load_frea_config(config.config_path)
    model_name = config.model or frea_cfg.get("model") or "kilo-auto/free"
    auto_approve = config.yes or frea_cfg.get("auto_approve", False)

    try:
        provider = get_provider(model_name)
    except Exception:
        provider = get_provider("kilo-auto/free")

    executor = ToolExecutor(auto_approve=auto_approve)
    agent = AgentLoop(provider=provider, executor=executor)
    session = SessionState(current_model=model_name)
    repl = InteractiveREPL(agent_loop=agent, session=session)
    return repl.run_repl()


def main() -> int:
    return run_cli(
        interactive_handler=interactive_run,
        headless_handler=headless_run,
    )


if __name__ == "__main__":
    sys.exit(main())
