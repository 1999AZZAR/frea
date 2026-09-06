# Technology Stack: Frea

## Core Platform
- **Language**: Python >= 3.10
- **Virtual Environment**: `.venv`
- **Dependencies**: Native standard library + `rich`, `prompt_toolkit`, `openai`, `google.generativeai` (Zero LangChain dependencies)
- **Operating System**: Linux (POSIX terminal environments)

## CLI & Terminal User Interface
- **TUI & Styling**: OpenCode theme palette, dual-tone block typography logo, `rich` for syntax diffs and tool cards
- **Prompt & Interaction**: `prompt_toolkit` for interactive prompt (`❯ `), command palette autocompletion (`/help`, `/status`, `/model`, `/compact`, `/clear`, `/exit`), history navigation, and live terminal statusline
- **Terminal Control**: POSIX terminal cursor manipulation, signal handlers (`SIGINT`, `SIGTERM`) for safe interruption

## AI Providers & Model Integration
- **OpenRouter (Default)**: `openrouter/auto` with automatic fallback to `openrouter/free`
- **Google GenAI**: `google-genai` / `google-generativeai`
- **OpenAI**: `openai` (GPT-4o, o3-mini)
- **Groq**: `groq` / OpenAI-compatible endpoint for ultra-low latency inference
- **Model Switching**: Dynamic provider switching via config or runtime slash command (`/model`)

## Agent Harness Architecture
- **Agent Loop**: Native ReAct tool executor supporting multi-turn reasoning and tool invocation
- **Tool Suite**:
  - Subprocess / Shell execution (`bash`) with timeout and output capture
  - Filesystem manipulation (read, write, targeted patch/diff)
  - Code search (`grep` / `ripgrep`, glob / `fd`)
  - Git status and diff inspection
- **Context Management**: Token-aware message history, prompt compaction, and rotating session logs

## Configuration & Persistence
- **Config Management**: OpenCode-compliant JSON configuration (`~/.config/frea/config.json` and `~/.config/frea/tui.json`, respecting `$XDG_CONFIG_HOME`) with CLI `--config` override, with fallback to legacy `config.ini`
- **Logging**: Python `logging` with `RotatingFileHandler` writing to `logs/`
- **Session State**: JSON-based session history and checkpointing

## Development & Code Hygiene
- **Git Hooks**: `pre-commit` (managing linting, syntax verification, secret detection, formatting)
- **Linter & Formatter**: `ruff`
- **Testing Framework**: `pytest`
