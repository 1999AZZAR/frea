"""Tool execution dispatcher and safety guardrails for Frea harness."""

from typing import Any, Callable, Dict, Optional
from src.tools import (
    ToolResult,
    bash_run,
    file_patch,
    file_read,
    file_write,
    find_files,
    grep_search,
)

DESTRUCTIVE_TOOLS = {"bash_run", "file_write", "file_patch"}


def default_confirm(tool_name: str, args: Dict[str, Any]) -> bool:
    """Prompt user on terminal for confirmation to execute high-impact tool."""
    from src.cards import render_permission_prompt
    from src.ui import console

    prompt = render_permission_prompt(tool_name, args)
    console.print(prompt, end="")
    response = input().strip().lower()
    return response in ("y", "yes")


class ToolExecutor:
    """Executes tools with safety checks and confirmation hooks."""

    def __init__(
        self,
        auto_approve: bool = False,
        confirm_fn: Optional[Callable[[str, Dict[str, Any]], bool]] = None,
    ):
        self.auto_approve = auto_approve
        self.confirm_fn = confirm_fn or default_confirm
        self.registry = {
            "bash_run": bash_run,
            "file_read": file_read,
            "file_write": file_write,
            "file_patch": file_patch,
            "grep_search": grep_search,
            "find_files": find_files,
        }

    def execute(self, tool_name: str, args: Dict[str, Any]) -> ToolResult:
        if tool_name not in self.registry:
            return ToolResult(success=False, error=f"Unknown tool: {tool_name}")

        if tool_name in DESTRUCTIVE_TOOLS and not self.auto_approve:
            if not self.confirm_fn(tool_name, args):
                return ToolResult(
                    success=False,
                    error="Execution rejected by user.",
                )

        fn = self.registry[tool_name]
        try:
            return fn(**args)
        except TypeError as err:
            return ToolResult(
                success=False,
                error=f"Invalid arguments for {tool_name}: {err}",
            )
        except Exception as exc:
            return ToolResult(
                success=False,
                error=f"Tool error in {tool_name}: {exc}",
            )
