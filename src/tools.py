"""Core agent execution tools for Frea harness (Kamui & OpenCode architecture)."""

from dataclasses import dataclass, field
import fnmatch
import os
from pathlib import Path
import re
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional
import uuid

MAX_COMMAND_OUTPUT = 32 * 1024  # 32KB output cap
MAX_SEARCH_OUTPUT = 16 * 1024  # 16KB search output cap
MAX_SEARCH_MATCHES = 200  # max matches returned by grep
MAX_READ_LINES = 2000

IGNORE_PATTERNS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
}


@dataclass
class ToolResult:
    """Standardized output result returned by all internal tools."""

    success: bool
    output: str = ""
    error: Optional[str] = None
    exit_code: int = 0


# --- File Operations ---


def read_file(
    path: str,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
) -> ToolResult:
    """Read UTF-8 text file content with optional line slicing and line numbers."""
    try:
        file_path = Path(path)
        if not file_path.is_file():
            return ToolResult(success=False, error=f"File not found: {path}")

        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        total_lines = len(lines)

        # Start_line/end_line compatibility
        if start_line is not None and offset is None:
            offset = start_line
        if end_line is not None and limit is None and offset is not None:
            limit = max(0, end_line - offset + 1)

        start = max(0, (offset - 1)) if offset and offset > 0 else 0
        end = (
            min(total_lines, start + limit)
            if limit is not None
            else min(total_lines, start + MAX_READ_LINES)
        )

        selected_lines = lines[start:end]
        output = "\n".join(
            f"{i + start + 1}: {line}" for i, line in enumerate(selected_lines)
        )
        if total_lines > end:
            output += f"\n... ({total_lines - end} more lines truncated)"

        return ToolResult(success=True, output=output)
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))


def write_file(path: str, content: str, overwrite: bool = True) -> ToolResult:
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
        byte_count = len(content.encode("utf-8"))
        line_count = len(content.splitlines())
        return ToolResult(
            success=True,
            output=f"Successfully wrote {path} ({byte_count} bytes, {line_count} lines)",
        )
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))


def patch_file(
    path: str,
    old_text: Optional[str] = None,
    new_text: Optional[str] = None,
    target: Optional[str] = None,
    replacement: Optional[str] = None,
) -> ToolResult:
    """Modify a file by replacing old_text (must match exactly once) with new_text.

    If old_text is empty or not provided and file does not exist, creates the file.
    """
    search_text = old_text if old_text is not None else target
    replace_text = new_text if new_text is not None else replacement

    if replace_text is None:
        return ToolResult(
            success=False, error="Missing replacement content ('new_text')"
        )

    try:
        file_path = Path(path)

        # Creation mode: empty old_text creates new file
        if not search_text:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(replace_text, encoding="utf-8")
            return ToolResult(success=True, output=f"Successfully created {path}")

        if not file_path.is_file():
            return ToolResult(success=False, error=f"File not found: {path}")

        content = file_path.read_text(encoding="utf-8")
        occurrences = content.count(search_text)

        if occurrences == 0:
            return ToolResult(
                success=False,
                error=f"Target string not found in {path}. Read the file to ensure exact match.",
            )
        if occurrences > 1:
            return ToolResult(
                success=False,
                error=f"Target string found {occurrences} times in {path}. Must match uniquely.",
            )

        new_content = content.replace(search_text, replace_text, 1)
        file_path.write_text(new_content, encoding="utf-8")
        return ToolResult(success=True, output=f"Successfully patched {path}")
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))


# --- Search & Discovery ---


def list_directory(path: str = ".", depth: int = 1) -> ToolResult:
    """List contents of directory relative to root, ignoring VCS/venv directories."""
    try:
        base = Path(path)
        if not base.exists():
            return ToolResult(success=False, error=f"Directory not found: {path}")
        if not base.is_dir():
            return ToolResult(success=False, error=f"Not a directory: {path}")

        entries: List[str] = []
        try:
            items = sorted(
                base.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())
            )
        except PermissionError as err:
            return ToolResult(success=False, error=f"Permission denied: {err}")

        for item in items:
            name = item.name
            if name.startswith(".") or name in IGNORE_PATTERNS:
                continue
            if item.is_dir():
                entries.append(f"{name}/")
            else:
                size = item.stat().st_size
                entries.append(f"{name} ({size} B)")

        output = "\n".join(entries) if entries else "(empty directory)"
        return ToolResult(success=True, output=output)
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))


def grep(
    query: str,
    path: str = ".",
    is_regex: bool = False,
    case_sensitive: bool = False,
) -> ToolResult:
    """Search for pattern across files with line numbers, respecting limits."""
    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.compile(query if is_regex else re.escape(query), flags=flags)
        base = Path(path)

        if not base.exists():
            return ToolResult(success=False, error=f"Path not found: {path}")

        if base.is_file():
            files_to_search = [base]
        else:
            files_to_search = []
            for p in base.rglob("*"):
                if p.is_file() and not any(
                    part.startswith(".") or part in IGNORE_PATTERNS for part in p.parts
                ):
                    files_to_search.append(p)

        matches: List[str] = []
        total_matched = 0

        for file_p in files_to_search:
            try:
                text = file_p.read_text(encoding="utf-8", errors="ignore")
                rel_path = str(file_p)
                for line_no, line in enumerate(text.splitlines(), start=1):
                    if pattern.search(line):
                        matches.append(f"{rel_path}:{line_no}: {line}")
                        total_matched += 1
                        if total_matched >= MAX_SEARCH_MATCHES:
                            break
                if total_matched >= MAX_SEARCH_MATCHES:
                    matches.append(f"... (reached max {MAX_SEARCH_MATCHES} matches)")
                    break
            except Exception:
                continue

        output = "\n".join(matches) if matches else "No matches found."
        if len(output) > MAX_SEARCH_OUTPUT:
            output = output[:MAX_SEARCH_OUTPUT] + "\n... (output truncated)"

        return ToolResult(success=True, output=output)
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))


def glob(pattern: str, path: str = ".") -> ToolResult:
    """Find files matching glob pattern starting from path, ignoring hidden/venv."""
    try:
        matches = []
        for root, dirs, files in os.walk(path):
            dirs[:] = [
                d for d in dirs if not d.startswith(".") and d not in IGNORE_PATTERNS
            ]
            for filename in files:
                if fnmatch.fnmatch(filename, pattern):
                    matches.append(os.path.join(root, filename))
        output = "\n".join(sorted(matches)) if matches else "No files matched pattern."
        return ToolResult(success=True, output=output)
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))


# --- Process Execution & Background Job Registry ---


@dataclass
class JobInfo:
    job_id: str
    command: str
    process: subprocess.Popen
    start_time: float
    output_lines: List[str] = field(default_factory=list)
    status: str = "running"  # "running", "completed", "failed", "terminated"
    exit_code: Optional[int] = None


class JobRegistry:
    """Thread-safe registry for background commands."""

    def __init__(self):
        self._jobs: Dict[str, JobInfo] = {}
        self._lock = threading.Lock()

    def register(self, command: str, proc: subprocess.Popen) -> str:
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        info = JobInfo(
            job_id=job_id,
            command=command,
            process=proc,
            start_time=time.time(),
        )
        with self._lock:
            self._jobs[job_id] = info

        # Launch output drainer thread
        def drain(p: subprocess.Popen, j_info: JobInfo):
            if p.stdout:
                for line in iter(p.stdout.readline, ""):
                    if not line:
                        break
                    with self._lock:
                        j_info.output_lines.append(line.rstrip())
            p.wait()
            with self._lock:
                j_info.exit_code = p.returncode
                if j_info.status == "running":
                    j_info.status = "completed" if p.returncode == 0 else "failed"

        t = threading.Thread(target=drain, args=(proc, info), daemon=True)
        t.start()
        return job_id

    def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            elapsed = time.time() - job.start_time
            if job.process.poll() is not None and job.status == "running":
                job.exit_code = job.process.returncode
                job.status = "completed" if job.exit_code == 0 else "failed"
            return {
                "job_id": job.job_id,
                "command": job.command,
                "status": job.status,
                "exit_code": job.exit_code,
                "elapsed_seconds": round(elapsed, 1),
                "output": "\n".join(job.output_lines),
            }

    def stop(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            if job.process.poll() is None:
                try:
                    job.process.terminate()
                    time.sleep(0.1)
                    if job.process.poll() is None:
                        job.process.kill()
                except Exception:
                    pass
            job.status = "terminated"
            job.exit_code = -15
            return True


_GLOBAL_JOB_REGISTRY = JobRegistry()


def run_command(
    command: str,
    cwd: Optional[str] = None,
    timeout: int = 30,
    background: bool = False,
) -> ToolResult:
    """Execute a shell command with timeout, output cap, and background support."""
    if background:
        try:
            proc = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            job_id = _GLOBAL_JOB_REGISTRY.register(command, proc)
            return ToolResult(
                success=True,
                output=f"Background job started with ID: {job_id} (PID: {proc.pid})",
            )
        except Exception as exc:
            return ToolResult(
                success=False,
                error=f"Failed to start background job: {exc}",
                exit_code=-1,
            )

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
        if len(output) > MAX_COMMAND_OUTPUT:
            output = output[:MAX_COMMAND_OUTPUT] + "\n... (output truncated)"
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


def command_status(job_id: str) -> ToolResult:
    """Query execution status and captured output of a background job."""
    info = _GLOBAL_JOB_REGISTRY.get_status(job_id)
    if not info:
        return ToolResult(success=False, error=f"Unknown background job ID: {job_id}")

    output_snippet = info["output"]
    if len(output_snippet) > MAX_COMMAND_OUTPUT:
        output_snippet = output_snippet[-MAX_COMMAND_OUTPUT:] + "\n... (tail truncated)"

    summary = (
        f"Job: {info['job_id']}\n"
        f"Status: {info['status']}\n"
        f"Exit Code: {info['exit_code']}\n"
        f"Elapsed: {info['elapsed_seconds']}s\n"
        f"Output:\n{output_snippet if output_snippet else '(no output yet)'}"
    )
    return ToolResult(success=True, output=summary)


def stop_command(job_id: str) -> ToolResult:
    """Terminate an active background job by ID."""
    stopped = _GLOBAL_JOB_REGISTRY.stop(job_id)
    if not stopped:
        return ToolResult(success=False, error=f"Unknown background job ID: {job_id}")
    return ToolResult(
        success=True, output=f"Successfully stopped and terminated job: {job_id}"
    )


# --- Plan & Multi-Step Checklist Management ---

_GLOBAL_SESSION_PLAN: List[Dict[str, str]] = []


def update_plan(plan: List[Dict[str, str]]) -> ToolResult:
    """Declare or update the structured plan checklist for multi-step tasks."""
    global _GLOBAL_SESSION_PLAN
    if not isinstance(plan, list):
        return ToolResult(
            success=False, error="Plan must be a list of step dictionaries."
        )

    validated_plan: List[Dict[str, str]] = []
    for item in plan:
        if not isinstance(item, dict) or "step" not in item:
            return ToolResult(
                success=False,
                error="Each plan item must be an object with 'step' and 'status'.",
            )
        status = item.get("status", "pending")
        if status not in ("pending", "in_progress", "completed", "failed"):
            status = "pending"
        validated_plan.append({"step": str(item["step"]), "status": status})

    _GLOBAL_SESSION_PLAN = validated_plan
    return ToolResult(success=True, output=f"ok ({len(validated_plan)} steps)")


def get_current_plan() -> List[Dict[str, str]]:
    """Retrieve active session checklist."""
    return list(_GLOBAL_SESSION_PLAN)


# --- Backward Compatibility Aliases ---
bash_run = run_command
file_read = read_file
file_write = write_file
file_patch = patch_file
grep_search = grep
find_files = glob
