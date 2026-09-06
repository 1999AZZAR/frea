# Specification: Remake Internal Tooling Suite from Scratch (Kamui & OpenCode Parity)

## Overview & Background
Frea requires a complete overhaul of its internal tool engine built from scratch, adopting the architecture of Kamui (`/home/azzar/project/TUI_Agent/kamui/src/tools.rs`) and OpenCode (`/home/azzar/project/TUI_Agent/opencode/packages/core/src/tool`). The new tooling suite will provide robust filesystem, search, command execution (with background job control), and plan management capabilities while strictly adhering to Frea's 3-dependency constraint (`openai`, `rich`, `prompt_toolkit`).

## Key Requirements & Tool Capabilities

### 1. File Inspection & Manipulation
- **`read_file`**: Read UTF-8 files with optional `offset` (1-based start line) and `limit` (max lines to read). Prefixes output with 1-based line numbers. Truncates output gracefully if exceeding 16KB / 2000 lines.
- **`write_file`**: Create new files or overwrite existing ones. Automatically creates parent directories. Returns line count and byte count written.
- **`patch_file`**: Surgical file editing matching Kamui's protocol:
  - If `old_text` is empty: writes `new_text` as a new file.
  - If `old_text` is non-empty: asserts exactly one unique match in target file and replaces it with `new_text`. Returns unified diff summary.
  - Fails with helpful diagnostics if 0 or >1 matches occur.

### 2. File Discovery & Pattern Matching
- **`list_directory`**: List directory contents relative to project root. Differentiates files and directories (trailing `/`), includes entry size, sorts hierarchically, and filters ignored directories (`.git`, `.venv`, `__pycache__`, `node_modules`).
- **`grep`**: Regex or literal pattern search across files with line numbers (`path:line: content`). Enforces max match limits (200 matches / 16KB output).
- **`glob`**: Wildcard path matching returning clean project-relative file paths.

### 3. Execution & Process Management
- **`run_command`**: Execute shell commands in POSIX bash with timeout (default 30s) and working directory control. Supports `background: true` to spawn async processes and return a `job_id`. Output capped at 16KB.
- **`command_status`**: Poll background job by `job_id`, returning running status, exit code, elapsed duration, and captured output stream.
- **`stop_command`**: Safely terminate/kill a running background job by `job_id`.

### 4. Plan & Multi-Step Coordination
- **`update_plan`**: Record or update structured checklist items (`step`: string, `status`: `pending` | `in_progress` | `completed`). Maintains session plan state for display in TUI.

### 5. Registry, Schemas & Agent Integration
- **`ToolDefinition` & `ToolRegistry`**: Generate valid OpenAI function schemas (`type: "function"`) so LLMs (OpenRouter, OpenCode, KiloCode, OpenAI, Groq) can invoke tools natively.
- **Confirmation Guardrails**: Interactive approval for destructive operations (`run_command`, `write_file`, `patch_file`) unless `--yes` / `auto_approve` is enabled.
- **`AgentLoop` Integration**: Supply tool schemas in LLM generation calls and dispatch tool responses iteratively back to conversation history.

## Non-Functional Requirements
- **Dependency Hygiene**: 100% Python standard library for subprocess, threading, regex, and filesystem operations. No external libraries beyond `openai`, `rich`, `prompt_toolkit`.
- **Safety & Robustness**: Resilient against path traversal outside project root where applicable, handles missing files and subprocess timeouts without uncaught crashes.
