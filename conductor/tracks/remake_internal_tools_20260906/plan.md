# Implementation Plan: Remake Internal Tooling Suite from Scratch

### Phase 1: Core File & Search Tooling [checkpoint: 2c71ef1]
- [x] Task: Write unit tests in `tests/test_tools_core.py` covering `read_file`, `write_file`, `patch_file`, `list_directory`, `grep`, and `glob` 2c71ef1
- [x] Task: Implement core file and search tools in `src/tools.py` matching Kamui/OpenCode specifications 2c71ef1
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) 2c71ef1

### Phase 2: Execution & Process Management [checkpoint: 2c71ef1]
- [x] Task: Write unit tests in `tests/test_tools_execution.py` covering foreground & background command execution, job tracking, status, stop, and `update_plan` 2c71ef1
- [x] Task: Implement `JobRegistry`, `run_command` (with async background job control), `command_status`, `stop_command`, and `update_plan` in `src/tools.py` 2c71ef1
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) 2c71ef1

### Phase 3: ToolRegistry, Schema Projection & AgentLoop Integration [checkpoint: cc11d16]
- [x] Task: Write tests in `tests/test_tool_registry.py` covering tool definitions, OpenAI schema generation, confirmation callbacks, and ReAct agent tool calling cc11d16
- [x] Task: Implement `ToolDefinition`, `ToolRegistry`, and refactor `ToolExecutor` in `src/executor.py` cc11d16
- [x] Task: Update `AgentLoop` in `src/agent.py` to supply tool schemas to provider and process tool calls seamlessly cc11d16
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) cc11d16

### Phase 4: Full System Verification, CLI & Regression Suite [checkpoint: cc11d16]
- [x] Task: Update existing tool/TUI test suites to ensure 100% regression test passage cc11d16
- [x] Task: Run full test suite, verify clean pre-commit hooks, and test live tool invocation via CLI cc11d16
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) cc11d16
