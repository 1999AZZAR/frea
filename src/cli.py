"""CLI argument parsing and configuration for Frea."""

from dataclasses import dataclass
import argparse
from typing import Optional, Sequence


@dataclass
class CLIConfig:
    prompt: Optional[str] = None
    model: Optional[str] = None
    yes: bool = False
    config_path: Optional[str] = None

    @property
    def is_interactive(self) -> bool:
        return self.prompt is None


def parse_args(argv: Optional[Sequence[str]] = None) -> CLIConfig:
    """Parse command line arguments into a CLIConfig object."""
    parser = argparse.ArgumentParser(
        prog="frea",
        description="Frea: Terminal-Native AI Coding Agent Harness",
    )
    parser.add_argument(
        "-p",
        "--prompt",
        "--run",
        dest="prompt",
        help="Run prompt in non-interactive batch mode and exit",
        default=None,
    )
    parser.add_argument(
        "-m",
        "--model",
        dest="model",
        help="Target AI model identifier (default: from ~/.config/frea/config.json or openrouter/auto)",
        default=None,
    )
    parser.add_argument(
        "-y",
        "--yes",
        dest="yes",
        action="store_true",
        help="Bypass interactive confirmation prompts for tool executions",
        default=False,
    )
    parser.add_argument(
        "-c",
        "--config",
        dest="config_path",
        help="Path to custom config.json file",
        default=None,
    )

    args = parser.parse_args(argv)
    return CLIConfig(
        prompt=args.prompt,
        model=args.model,
        yes=args.yes,
        config_path=args.config_path,
    )
