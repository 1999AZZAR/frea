"""Tool execution dispatcher, schema registry, and safety guardrails for Frea."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from src.tools import (
    ToolResult,
    bash_run,
    command_status,
    file_patch,
    file_read,
    file_write,
    find_files,
    glob,
    grep,
    grep_search,
    list_directory,
    patch_file,
    read_file,
    run_command,
    stop_command,
    update_plan,
    write_file,
)

DESTRUCTIVE_TOOLS = {
    "run_command",
    "write_file",
    "patch_file",
    "bash_run",
    "file_write",
    "file_patch",
}


@dataclass
class ToolDefinition:
    """Formal specification and callable binding for an agent tool."""

    name: str
    description: str
    parameters: Dict[str, Any]
    func: Callable[..., ToolResult]
    requires_confirmation: bool = False

    def to_openai_schema(self) -> Dict[str, Any]:
        """Project tool into OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    """Registry maintaining active tool definitions and OpenAI projection."""

    def __init__(self, tools: Optional[Dict[str, ToolDefinition]] = None):
        self._tools: Dict[str, ToolDefinition] = tools or {}
        self._mcp_clients: List[Any] = []

    def register(self, definition: ToolDefinition) -> None:
        self._tools[definition.name] = definition

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def register_mcp_client(self, client: Any) -> None:
        """Register tools exposed by an MCP client instance."""
        self._mcp_clients.append(client)
        server_name = getattr(client.config, "name", "mcp")
        try:
            tools_list = client.list_tools()
            for t in tools_list:
                t_name = t.get("name")
                if not t_name:
                    continue
                full_name = f"{server_name}_{t_name}"
                desc = t.get("description", f"MCP tool from {server_name}")
                params = t.get("inputSchema") or {"type": "object", "properties": {}}

                def make_caller(cl, tool_inner):
                    return lambda **kwargs: cl.call_tool(tool_inner, kwargs)

                self.register(
                    ToolDefinition(
                        name=full_name,
                        description=desc,
                        parameters=params,
                        func=make_caller(client, t_name),
                        requires_confirmation=False,
                    )
                )
        except Exception:
            pass

    def stop_all_mcp(self) -> None:
        """Stop all connected MCP clients."""
        for client in self._mcp_clients:
            try:
                client.stop()
            except Exception:
                pass

    def to_openai_tools(self) -> List[Dict[str, Any]]:
        """Return list of OpenAI function definitions for primary tools, skills, and MCP."""
        primary_tool_names = [
            "read_file",
            "write_file",
            "patch_file",
            "list_directory",
            "grep",
            "glob",
            "run_command",
            "command_status",
            "stop_command",
            "update_plan",
            "skill",
        ]
        schemas = []
        seen = set()
        for name in primary_tool_names:
            defn = self._tools.get(name)
            if defn and defn.name not in seen:
                schemas.append(defn.to_openai_schema())
                seen.add(defn.name)

        # Include registered MCP tools
        for name, defn in self._tools.items():
            if name not in seen and not any(
                name.startswith(p)
                for p in [
                    "bash_run",
                    "file_read",
                    "file_write",
                    "file_patch",
                    "grep_search",
                    "find_files",
                ]
            ):
                schemas.append(defn.to_openai_schema())
                seen.add(name)

        return schemas

    @classmethod
    def with_defaults(
        cls,
        include_skills: bool = True,
        include_mcp: bool = True,
        search_paths: Optional[List[Path]] = None,
    ) -> "ToolRegistry":
        """Scaffold standard Kamui & OpenCode tool definitions."""
        registry = cls()

        registry.register(
            ToolDefinition(
                name="read_file",
                description="Read UTF-8 text file content with line numbers. Optionally slice with offset (1-based start line) and limit (number of lines).",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file to read relative to project root.",
                        },
                        "offset": {
                            "type": "integer",
                            "description": "1-based starting line number to read from.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of lines to read.",
                        },
                    },
                    "required": ["path"],
                },
                func=read_file,
                requires_confirmation=False,
            )
        )

        registry.register(
            ToolDefinition(
                name="write_file",
                description="Write content to a file, creating parent directories if needed. Overwrites existing file if overwrite is True.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file to create or overwrite.",
                        },
                        "content": {
                            "type": "string",
                            "description": "Full text content to write into the file.",
                        },
                        "overwrite": {
                            "type": "boolean",
                            "description": "Whether to replace existing file contents (default: true).",
                        },
                    },
                    "required": ["path", "content"],
                },
                func=write_file,
                requires_confirmation=True,
            )
        )

        registry.register(
            ToolDefinition(
                name="patch_file",
                description="Modify one file by replacing old_text (must match exactly once) with new_text. Pass empty old_text to create a new file.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path of the file to modify or create.",
                        },
                        "old_text": {
                            "type": "string",
                            "description": "Exact text to replace (must match uniquely). Empty to create new file.",
                        },
                        "new_text": {
                            "type": "string",
                            "description": "Replacement text, or full content of new file.",
                        },
                    },
                    "required": ["path", "old_text", "new_text"],
                },
                func=patch_file,
                requires_confirmation=True,
            )
        )

        registry.register(
            ToolDefinition(
                name="list_directory",
                description="List entries of a directory in the project. Directories end with a trailing slash.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path relative to project root (default: '.').",
                        },
                        "depth": {
                            "type": "integer",
                            "description": "Max recursion depth to list entries (default: 1).",
                        },
                    },
                    "required": [],
                },
                func=list_directory,
                requires_confirmation=False,
            )
        )

        registry.register(
            ToolDefinition(
                name="grep",
                description="Search for matching strings or regex patterns across project files, returning matching lines with file and line number.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Literal text or regex pattern to search for.",
                        },
                        "path": {
                            "type": "string",
                            "description": "Path or directory to search within (default: '.').",
                        },
                        "is_regex": {
                            "type": "boolean",
                            "description": "Whether query is a regex pattern (default: false).",
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "description": "Whether match is case-sensitive (default: false).",
                        },
                    },
                    "required": ["query"],
                },
                func=grep,
                requires_confirmation=False,
            )
        )

        registry.register(
            ToolDefinition(
                name="glob",
                description="Find files matching wildcard glob pattern relative to project path.",
                parameters={
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Glob pattern to match, e.g. '*.py' or '**/*.json'.",
                        },
                        "path": {
                            "type": "string",
                            "description": "Directory path to begin search (default: '.').",
                        },
                    },
                    "required": ["pattern"],
                },
                func=glob,
                requires_confirmation=False,
            )
        )

        registry.register(
            ToolDefinition(
                name="run_command",
                description="Execute a shell command with timeout and output capture. Set background=true to run asynchronously.",
                parameters={
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "POSIX bash command line to execute.",
                        },
                        "cwd": {
                            "type": "string",
                            "description": "Working directory to execute command within.",
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Command timeout in seconds (default: 30).",
                        },
                        "background": {
                            "type": "boolean",
                            "description": "Whether to launch as background async job (default: false).",
                        },
                    },
                    "required": ["command"],
                },
                func=run_command,
                requires_confirmation=True,
            )
        )

        registry.register(
            ToolDefinition(
                name="command_status",
                description="Query execution status and captured stdout/stderr of a background job.",
                parameters={
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "Job identifier returned by run_command(background=True).",
                        },
                    },
                    "required": ["job_id"],
                },
                func=command_status,
                requires_confirmation=False,
            )
        )

        registry.register(
            ToolDefinition(
                name="stop_command",
                description="Safely terminate an active background job.",
                parameters={
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "Job identifier to terminate.",
                        },
                    },
                    "required": ["job_id"],
                },
                func=stop_command,
                requires_confirmation=True,
            )
        )

        registry.register(
            ToolDefinition(
                name="update_plan",
                description="Declare or update the checklist for a multi-step task, visible to the user as a live plan.",
                parameters={
                    "type": "object",
                    "properties": {
                        "plan": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "step": {"type": "string"},
                                    "status": {
                                        "type": "string",
                                        "enum": [
                                            "pending",
                                            "in_progress",
                                            "completed",
                                            "failed",
                                        ],
                                    },
                                },
                                "required": ["step"],
                            },
                        },
                    },
                    "required": ["plan"],
                },
                func=update_plan,
                requires_confirmation=False,
            )
        )

        # Register backward compatibility aliases
        registry.register(
            ToolDefinition(
                name="bash_run",
                description="Execute bash command (legacy alias).",
                parameters={
                    "type": "object",
                    "properties": {"command": {"type": "string"}},
                    "required": ["command"],
                },
                func=bash_run,
                requires_confirmation=True,
            )
        )
        registry.register(
            ToolDefinition(
                name="file_read",
                description="Read file content (legacy alias).",
                parameters={
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
                func=file_read,
                requires_confirmation=False,
            )
        )
        registry.register(
            ToolDefinition(
                name="file_write",
                description="Write file content (legacy alias).",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                },
                func=file_write,
                requires_confirmation=True,
            )
        )
        registry.register(
            ToolDefinition(
                name="file_patch",
                description="Patch file content (legacy alias).",
                parameters={
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
                func=file_patch,
                requires_confirmation=True,
            )
        )
        registry.register(
            ToolDefinition(
                name="grep_search",
                description="Search file content (legacy alias).",
                parameters={
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
                func=grep_search,
                requires_confirmation=False,
            )
        )
        registry.register(
            ToolDefinition(
                name="find_files",
                description="Find files (legacy alias).",
                parameters={
                    "type": "object",
                    "properties": {"pattern": {"type": "string"}},
                    "required": ["pattern"],
                },
                func=find_files,
                requires_confirmation=False,
            )
        )

        if include_skills:
            try:
                from src.skills import discover_skills, load_skill

                discovered = discover_skills(search_paths=search_paths)
                registry.register(
                    ToolDefinition(
                        name="skill",
                        description="Load a specialized skill when the task matches one of the available skills in the system context. Injects skill instructions and files into conversation.",
                        parameters={
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name of the skill to load from available skills.",
                                }
                            },
                            "required": ["name"],
                        },
                        func=lambda name: load_skill(name, skills=discovered),
                        requires_confirmation=False,
                    )
                )
            except Exception:
                pass

        if include_mcp:
            try:
                from src.mcp import load_user_mcp_servers

                mcp_servers = load_user_mcp_servers()
                for client in mcp_servers.values():
                    registry.register_mcp_client(client)
            except Exception:
                pass

        return registry


def default_confirm(tool_name: str, args: Dict[str, Any]) -> bool:
    """Prompt user on terminal for confirmation to execute high-impact tool."""
    from src.cards import render_permission_prompt
    from src.ui import console

    prompt = render_permission_prompt(tool_name, args)
    console.print(prompt, end="")
    response = input().strip().lower()
    return response in ("y", "yes")


class ToolExecutor:
    """Executes tools with safety checks, confirmation hooks, and schema access."""

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        auto_approve: bool = False,
        confirm_fn: Optional[Callable[[str, Dict[str, Any]], bool]] = None,
    ):
        self.registry = registry or ToolRegistry.with_defaults()
        self.auto_approve = auto_approve
        self.confirm_fn = confirm_fn or default_confirm

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Return registered tools as OpenAI tool definitions."""
        return self.registry.to_openai_tools()

    def execute(self, tool_name: str, args: Dict[str, Any]) -> ToolResult:
        defn = self.registry.get(tool_name)
        if not defn:
            return ToolResult(success=False, error=f"Unknown tool: {tool_name}")

        if defn.requires_confirmation and not self.auto_approve:
            if not self.confirm_fn(tool_name, args):
                return ToolResult(
                    success=False,
                    error="Execution rejected by user.",
                )

        try:
            return defn.func(**args)
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
