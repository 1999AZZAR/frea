"""CLI execution runner and process lifecycle management for Frea."""

import signal
import sys
from typing import Callable, Optional, Sequence
from src.cli import CLIConfig, parse_args
from src.utils import cursor_show


def setup_signal_handlers(cleanup_fn: Optional[Callable[[], None]] = None) -> None:
    """Register signal handlers to restore terminal state on interrupts."""

    def _sig_handler(signum: int, frame) -> None:
        cursor_show()
        if cleanup_fn:
            cleanup_fn()
        sys.exit(128 + signum)

    try:
        signal.signal(signal.SIGINT, _sig_handler)
        signal.signal(signal.SIGTERM, _sig_handler)
    except (ValueError, AttributeError):
        pass


def run_cli(
    argv: Optional[Sequence[str]] = None,
    interactive_handler: Optional[Callable[[CLIConfig], int]] = None,
    headless_handler: Optional[Callable[[CLIConfig], int]] = None,
) -> int:
    """Entry point to parse CLI arguments and route to appropriate handler."""
    config = parse_args(argv)
    setup_signal_handlers()

    if config.is_interactive:
        if interactive_handler:
            return interactive_handler(config)
        return 0
    else:
        if headless_handler:
            return headless_handler(config)
        return 0
