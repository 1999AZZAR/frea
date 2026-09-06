# Implementation Plan: Skills & Model Context Protocol (MCP) Integration

### Phase 1: Skills Discovery & Injection (`src/skills.py`)
- [ ] Task: Write unit tests in `tests/test_skills.py` for skill discovery, frontmatter parsing, prompt projection, and the `skill` tool
- [ ] Task: Implement `src/skills.py` with `SkillInfo`, `discover_skills()`, `render_skills_prompt()`, and `execute_skill_tool()`
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

### Phase 2: Stdio MCP Client & Server Manager (`src/mcp.py`)
- [ ] Task: Write unit tests in `tests/test_mcp.py` testing JSON-RPC 2.0 handshake, `tools/list` schema extraction, and `tools/call` dispatch
- [ ] Task: Implement stdio JSON-RPC MCP client and server manager in `src/mcp.py` using Python standard library
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

### Phase 3: Unification with ToolRegistry & AgentLoop
- [ ] Task: Write integration tests in `tests/test_mcp_skills_integration.py` verifying AgentLoop with internal, skill, and MCP tools
- [ ] Task: Integrate Skills and MCP servers into `ToolRegistry` in `src/executor.py` and `AgentLoop` in `src/agent.py`
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

### Phase 4: Full System Verification & End-to-End Regression
- [ ] Task: Run full test suite (`pytest`), verify clean `pre-commit` across all files, and verify live execution
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
