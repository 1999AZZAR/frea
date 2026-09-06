# Track Specification: Modernize Frea Agent Harness

## Overview
Modernize Frea from an early-stage prompt chat utility into a production-grade, terminal-native AI coding agent harness inspired by OpenCode CLI and Claude Code. The modernized Frea implements an autonomous ReAct reasoning-action loop, native tool execution (bash, file read/write/patch, grep, find), dual interactive and headless CLI invocation modes, safety guardrails, and clean terminal visual rendering.

## Functional Requirements
- **CLI & Invocation Modes**:
  - Interactive REPL: Full interactive terminal session with readline navigation, multi-line input, slash commands (`/help`, `/model`, `/clear`, `/exit`).
  - Headless / Batch Mode: Execute prompt non-interactively (`frea -p "instruction"` or `frea --run "instruction"`) and stream output to stdout, enabling pipe integration.
- **Agentic ReAct Loop**:
  - Multi-turn execution loop: Model produces thought & tool calls -> Harness executes tools -> Results fed back to model -> Repeats until completion.
  - Multi-provider model client: Clean abstraction over Google GenAI, OpenAI, and Groq with unified tool-calling schema.
- **Core Tool Suite**:
  - `bash_run`: Subprocess execution with timeout, streaming output capture, working directory control, and exit code checking.
  - `file_read`: View file contents with line range slicing.
  - `file_write`: Atomic file creation and full overwrite.
  - `file_patch`: Targeted contiguous chunk replacement.
  - `grep_search`: Pattern and regex search across workspace files.
  - `find_files`: Workspace file and path discovery.
- **Safety & Permissions**:
  - Interactive confirmation prompt before executing high-impact bash commands or file modifications.
  - `--yes` / `-y` flag to bypass interactive confirmations in headless/scripted modes.
  - Signal handling (`Ctrl+C`): Clean abort of active tool execution while keeping terminal state and cursor intact.

## Non-Functional Requirements
- **Performance & Efficiency**: Minimal token consumption using concise tool schemas and compressed outputs (Caveman/RTK principles).
- **Zero Terminal Drift**: Proper terminal escape sequences, guaranteed cursor visibility recovery (`cursor_show()`) on exit or errors.
- **Maintainability**: Modular package layout under `src/frea/` replacing monolithic code scripts.

## Acceptance Criteria
- [ ] `frea` launches interactive REPL with slash command support and readline editing.
- [ ] `frea -p "query"` executes headless tool loops and outputs result cleanly.
- [ ] ReAct agent loop successfully invokes tools, ingests output, and solves multi-step file tasks.
- [ ] Safety prompts intercept destructive bash/file actions unless `-y` is provided.
- [ ] All unit tests pass with coverage >80% under `pytest`.

## Out of Scope
- GUI/Web-based dashboards (Frea is strictly terminal-native).
- Remote cloud sandbox provisioning (runs locally with POSIX controls).
