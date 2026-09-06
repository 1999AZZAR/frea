from unittest.mock import MagicMock
from src.runner import run_cli, setup_signal_handlers


def test_setup_signal_handlers():
    """Verify signal handlers can be registered without error."""
    cleanup_mock = MagicMock()
    setup_signal_handlers(cleanup_fn=cleanup_mock)
    # Verification that it runs cleanly


def test_run_cli_dispatches_interactive():
    """Verify run_cli dispatches to interactive mode when no prompt is provided."""
    interactive_fn = MagicMock(return_value=0)
    headless_fn = MagicMock(return_value=0)

    exit_code = run_cli(
        argv=[],
        interactive_handler=interactive_fn,
        headless_handler=headless_fn,
    )
    assert exit_code == 0
    interactive_fn.assert_called_once()
    headless_fn.assert_not_called()


def test_run_cli_dispatches_headless():
    """Verify run_cli dispatches to headless mode when prompt is provided."""
    interactive_fn = MagicMock(return_value=0)
    headless_fn = MagicMock(return_value=0)

    exit_code = run_cli(
        argv=["-p", "test task", "--yes"],
        interactive_handler=interactive_fn,
        headless_handler=headless_fn,
    )
    assert exit_code == 0
    interactive_fn.assert_not_called()
    headless_fn.assert_called_once()
    config = headless_fn.call_args[0][0]
    assert config.prompt == "test task"
    assert config.yes is True
