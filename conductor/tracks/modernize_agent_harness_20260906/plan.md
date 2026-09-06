# Implementation Plan: Modernize Frea Agent Harness

## Phase 1: CLI Entry Point & Execution Dispatch [checkpoint: d223ee4]
- [x] Task: Write tests for CLI argument parser and mode dispatcher [472c704]
    - [x] Create tests for `-p` / `--run` headless flag handling
    - [x] Create tests for `--model`, `--yes` flags and default interactive mode
- [x] Task: Implement modular CLI runner and signal handlers [d223ee4]
    - [x] Implement argument parsing with `argparse`
    - [x] Implement POSIX signal handlers (`SIGINT`, `SIGTERM`) with terminal cursor safety
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) [d223ee4]

## Phase 2: Core Tool Execution Engine & Safety Guardrails [checkpoint: 9cb072b]
- [x] Task: Write tests for tool execution suite [b9fe7e7]
    - [x] Create unit tests for `bash_run` with timeouts and directory sandboxing
    - [x] Create unit tests for `file_read`, `file_write`, and contiguous `file_patch`
    - [x] Create unit tests for `grep_search` and `find_files`
- [x] Task: Implement tool execution engine with interactive guardrails [9cb072b]
    - [x] Implement safe subprocess execution with captured stdout/stderr
    - [x] Implement file inspection and atomic modification tools
    - [x] Implement safety confirmation prompt interceptor with `--yes` override
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) [9cb072b]

## Phase 3: Agentic ReAct Engine & Model Provider Interface [checkpoint: 53c459c]
- [x] Task: Write tests for agent loop and model adapters [e85f2c7]
    - [x] Create unit tests for ReAct state transitions and tool call parsing
    - [x] Create mock tests for Gemini, OpenAI, and Groq provider adapters
- [x] Task: Implement agent reasoning loop and provider clients [53c459c]
    - [x] Implement unified provider abstraction layer
    - [x] Implement ReAct execution engine supporting iterative tool calling
    - [x] Implement prompt builder and context compaction
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) [53c459c]

## Phase 4: Interactive TUI & Slash Commands [checkpoint: dfcf48f]
- [x] Task: Write tests for interactive command parser and session manager [0fa3ba8]
    - [x] Create unit tests for slash commands (`/help`, `/model`, `/clear`, `/exit`)
    - [x] Create unit tests for rotating log management and session history
- [x] Task: Implement interactive TUI and command palette [dfcf48f]
    - [x] Implement readline-powered REPL with multi-line input support
    - [x] Implement slash command handlers and model switcher
    - [x] Integrate ANSI progress spinners and formatted output
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) [dfcf48f]

## Phase 5: End-to-End Integration & Regression Testing [checkpoint: 7c187a9]
- [x] Task: Write end-to-end integration tests [c818a8d]
    - [x] Test headless run flow executing a multi-step tool sequence
    - [x] Test interactive session initialization and graceful exit
- [x] Task: Execute full test suite and quality audit [7c187a9]
    - [x] Verify test suite passes with code coverage >80%
    - [x] Run pre-commit hooks across codebase
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) [7c187a9]
