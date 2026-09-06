# Technology Stack: Frea

## Core Platform
- **Language**: Python >= 3.10
- **Virtual Environment**: `.venv`
- **Dependencies**: Exactly 3 production dependencies: `openai`, `rich`, `prompt_toolkit` (Zero LangChain, Zero Google GenAI SDK)
- **Operating System**: Linux (POSIX terminal environments)

## CLI & Terminal User Interface
- **TUI & Styling**: OpenCode theme palette, dual-tone block typography logo, `rich` for syntax diffs and tool cards
- **Prompt & Interaction**: `prompt_toolkit` for interactive prompt (`❯ `), command palette autocompletion (`/help`, `/status`, `/model`, `/compact`, `/clear`, `/exit`), history navigation, and live terminal statusline
- **Terminal Control**: POSIX terminal cursor manipulation, signal handlers (`SIGINT`, `SIGTERM`) for safe interruption

## AI Providers & Model Integration
- **OpenRouter (Default)**: `openrouter/auto` with fallback to `openrouter/free` and free `opencode` gateway
- **OpenCode Free Gateway**: Keyless out-of-the-box provider (`https://api.opencode.ai/v1`, models `kimi-k2.5-free`, `deepseek-v4-flash:free`, `glm-4.7-flash-free`)
- **KiloCode Gateway**: Keyless out-of-the-box provider (`https://api.kilo.ai/api/gateway`, models `kilocode/kilo-auto/balanced`, `kilo/free`)
- **Google Gemini**: Direct OpenAI-compatible endpoint (`https://generativelanguage.googleapis.com/v1beta/openai/`) without `google-generativeai` SDK
- **OpenAI**: Standard `openai` endpoints (GPT-4o, o3-mini)
- **Groq**: Ultra-low latency inference via OpenAI-compatible endpoint
- **Model Switching**: Dynamic provider switching via config or runtime slash command (`/model`)

## Agent Harness & Tooling Architecture
- **Agent Loop**: Native ReAct tool executor supporting multi-turn reasoning and tool invocation with dynamic OpenAPI tool schema projection
- **Core Tool Suite (Kamui & OpenCode Parity)**:
  - File Operations: `read_file` (with line slicing/bounds), `write_file` (with dir creation), `patch_file` (surgical exact replacement)
  - Search & Discovery: `list_directory` (ignoring VCS/venv), `grep` (pattern search with line numbers), `glob` (wildcard matching)
  - Process & Jobs: `run_command` (foreground and detached background execution), `command_status`, `stop_command`
  - Plan Tracking: `update_plan` (multi-step structured task checklist)
- **Skills System (OpenCode Parity)**:
  - Dynamic discovery from `.agents/skills`, `~/.config/frea/skills`, `~/.agents/skills`
  - Automatic prompt injection (`<skills>`) and `skill` loader tool
- **Model Context Protocol (MCP)**:
  - Stdio transport client implementing JSON-RPC 2.0 (`initialize`, `tools/list`, `tools/call`)
  - Config-driven server integration (`mcpServers` in `config.json` or `mcp.json`)
  - Automatic tool namespacing (`{server}_{tool}`) into `ToolRegistry`
- **Context Management**: Token-aware message history, prompt compaction, and rotating session logs

## Configuration & Persistence
- **Config Management**: OpenCode-compliant JSON configuration (`~/.config/frea/config.json` and `~/.config/frea/tui.json`, respecting `$XDG_CONFIG_HOME`) with CLI `--config` override, with fallback to legacy `config.ini`
- **Logging**: Python `logging` with `RotatingFileHandler` writing to `logs/`
- **Session State**: JSON-based session history and checkpointing

## Development & Code Hygiene
- **Git Hooks**: `pre-commit` (managing linting, syntax verification, secret detection, formatting)
- **Linter & Formatter**: `ruff`
- **Testing Framework**: `pytest`
