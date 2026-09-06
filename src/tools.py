"""Core agent execution tools for Frea harness."""

from dataclasses import dataclass
import fnmatch
import os
from pathlib import Path
import re
import subprocess
from typing import Optional


@dataclass
class ToolResult:
    success: bool
    output: str = ""
    error: Optional[str] = None
    exit_code: int = 0


def bash_run(command: str, cwd: Optional[str] = None, timeout: int = 30) -> ToolResult:
    """Execute a bash shell command with timeout and captured output."""
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        success = proc.returncode == 0
        output = proc.stdout
        error = proc.stderr if not success else None
        return ToolResult(
            success=success,
            output=output,
            error=error,
            exit_code=proc.returncode,
        )
    except subprocess.TimeoutExpired:
        return ToolResult(
            success=False,
            error=f"Command timed out after {timeout} seconds",
            exit_code=-1,
        )
    except Exception as exc:
        return ToolResult(
            success=False,
            error=str(exc),
            exit_code=-1,
        )


def file_read(
    path: str, start_line: Optional[int] = None, end_line: Optional[int] = None
) -> ToolResult:
    """Read file content with optional 1-based start_line and end_line bounds."""
    try:
        file_path = Path(path)
        if not file_path.is_file():
            return ToolResult(success=False, error=f"File not found: {path}")

        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        total_lines = len(lines)

        start = (start_line - 1) if start_line and start_line > 0 else 0
        end = end_line if end_line and end_line <= total_lines else total_lines

        selected_lines = lines[start:end]
        output = "\n".join(
            f"{i + start + 1}: {line}" for i, line in enumerate(selected_lines)
        )
        return ToolResult(success=True, output=output)
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))


def file_write(path: str, content: str, overwrite: bool = False) -> ToolResult:
    """Write content to a file, creating parent directories if needed."""
    try:
        file_path = Path(path)
        if file_path.exists() and not overwrite:
            return ToolResult(
                success=False,
                error=f"File already exists: {path}. Set overwrite=True to replace.",
            )

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return ToolResult(success=True, output=f"Successfully wrote {path}")
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))


def file_patch(path: str, target: str, replacement: str) -> ToolResult:
    """Replace an exact contiguous match of target with replacement in a file."""
    try:
        file_path = Path(path)
        if not file_path.is_file():
            return ToolResult(success=False, error=f"File not found: {path}")

        content = file_path.read_text(encoding="utf-8")
        occurrences = content.count(target)

        if occurrences == 0:
            return ToolResult(success=False, error="Target string not found in file")
        if occurrences > 1:
            return ToolResult(
                success=False,
                error=f"Target string found {occurrences} times. Must match uniquely.",
            )

        new_content = content.replace(target, replacement, 1)
        file_path.write_text(new_content, encoding="utf-8")
        return ToolResult(success=True, output=f"Successfully patched {path}")
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))


def grep_search(query: str, path: str = ".", is_regex: bool = False) -> ToolResult:
    """Search for matching strings or patterns across files in path."""
    try:
        results = []
        pattern = re.compile(query if is_regex else re.escape(query))
        base_path = Path(path)

        if base_path.is_file():
            files_to_search = [base_path]
        else:
            files_to_search = [
                p
                for p in base_path.rglob("*")
                if p.is_file() and not any(part.startswith(".") for part in p.parts)
            ]

        for file_p in files_to_search:
            try:
                text = file_p.read_text(encoding="utf-8", errors="ignore")
                for line_no, line in enumerate(text.splitlines(), start=1):
                    if pattern.search(line):
                        results.append(f"{file_p}:{line_no}: {line}")
            except Exception:
                continue

        return ToolResult(
            success=True,
            output="\n".join(results) if results else "No matches found.",
        )
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))


def find_files(pattern: str, path: str = ".") -> ToolResult:
    """Find files matching glob pattern starting from path."""
    try:
        matches = []
        for root, dirs, files in os.walk(path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for filename in files:
                if fnmatch.fnmatch(filename, pattern):
                    matches.append(os.path.join(root, filename))
        return ToolResult(
            success=True,
            output="\n".join(matches) if matches else "No files matched pattern.",
        )
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))
