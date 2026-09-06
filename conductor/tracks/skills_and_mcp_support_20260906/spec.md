# Specification: Skills and Model Context Protocol (MCP) Integration

## Overview & Background
Frea requires robust support for Skills and Model Context Protocol (MCP) servers, implementing the proven architecture from OpenCode (`packages/core/src/skill.ts`, `packages/core/src/tool/skill.ts`, and `packages/opencode/src/mcp/index.ts`). This allows Frea to dynamically discover and inject specialized capabilities and integrate with local/remote MCP tool servers while maintaining zero extra external dependencies (using Python standard library for stdio JSON-RPC and YAML parsing).

## Architecture & Requirements

### 1. Skills System (OpenCode Parity)
- **Discovery**:
  - Scan directory sources in order of precedence:
    1. Workspace/Project `.agents/skills/`
    2. User configuration `~/.config/frea/skills/`
    3. Global `~/.agents/skills/`
  - Each skill is a directory containing `SKILL.md`.
  - Extract YAML frontmatter (`name`, `description`) and body content.
- **Context Injection**:
  - Expose summary of available skills to the LLM in system prompt or system instructions:
    `<skills>\n- {name}: {description}\n</skills>`.
- **`skill` Tool (`SkillTool`)**:
  - Input: `name: str`
  - Output: Full content wrapped in `<skill_content name="{name}">\n# Skill: {name}\n\n{content}\n\nBase directory: {dir}\n</skill_content>` along with listing of files in the skill directory.

### 2. Model Context Protocol (MCP) Client
- **Configuration**:
  - Support `mcpServers` defined in `~/.config/frea/config.json` or `~/.config/frea/mcp.json`.
  - Schema:
    ```json
    {
      "mcpServers": {
        "server_name": {
          "command": "python3",
          "args": ["path/to/server.py"],
          "env": { "KEY": "VAL" }
        }
      }
    }
    ```
- **Stdio Transport & JSON-RPC 2.0 Protocol**:
  - Pure Python stdlib subprocess client communicating over `stdin`/`stdout`.
  - Handshake: Send `initialize` request with client capabilities and receive server capabilities.
  - Discovery: Query `tools/list` to fetch available tools with descriptions and JSON schema parameters.
  - Namespacing: Tools registered into Frea's `ToolRegistry` with `{server_name}_{tool_name}`.
  - Dispatch: Send `tools/call` with arguments, collect response `content` (text, errors), and return `ToolResult`.

### 3. Tool Usage, Dispatch & Response Pipeline
- Seamless unification of:
  1. Core internal tools (`read_file`, `write_file`, `patch_file`, `list_directory`, `grep`, `glob`, `run_command`, `command_status`, `stop_command`, `update_plan`)
  2. Skills loader tool (`skill`)
  3. External MCP tools (`{server}_{tool}`)
- All tools project valid OpenAI function calling schemas (`to_openai_tools()`).
- Error containment: If an MCP server disconnects or fails, it returns a graceful `ToolResult(success=False, error=...)` without terminating the agent loop.

## Constraints
- Strictly preserve the 3 production dependencies (`openai`, `rich`, `prompt_toolkit`).
- Use standard library for subprocess, json, threading, and regex.
