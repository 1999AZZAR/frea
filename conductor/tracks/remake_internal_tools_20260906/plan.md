# Implementation Plan: Remake Internal Tooling Suite from Scratch

### Phase 1: Core File & Search Tooling
- [ ] Task: Write unit tests in `tests/test_tools_core.py` covering `read_file`, `write_file`, `patch_file`, `list_directory`, `grep`, and `glob`
- [ ] Task: Implement core file and search tools in `src/tools.py` matching Kamui/OpenCode specifications
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

### Phase 2: Execution & Process Management
- [ ] Task: Write unit tests in `tests/test_tools_execution.py` covering foreground & background command execution, job tracking, status, stop, and `update_plan`
- [ ] Task: Implement `JobRegistry`, `run_command` (with async background job control), `command_status`, `stop_command`, and `update_plan` in `src/tools.py`
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

### Phase 3: ToolRegistry, Schema Projection & AgentLoop Integration
- [ ] Task: Write tests in `tests/test_tool_registry.py` covering tool definitions, OpenAI schema generation, confirmation callbacks, and ReAct agent tool calling
- [ ] Task: Implement `ToolDefinition`, `ToolRegistry`, and refactor `ToolExecutor` in `src/executor.py`
- [ ] Task: Update `AgentLoop` in `src/agent.py` to supply tool schemas to provider and process tool calls seamlessly
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

### Phase 4: Full System Verification, CLI & Regression Suite
- [ ] Task: Update existing tool/TUI test suites to ensure 100% regression test passage
- [ ] Task: Run full test suite, verify clean pre-commit hooks, and test live tool invocation via CLI
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
