# Implementation Plan: Skills & Model Context Protocol (MCP) Integration

### Phase 1: Skills Discovery & Injection (`src/skills.py`) [checkpoint: 3a110e3]
- [x] Task: Write unit tests in `tests/test_skills.py` for skill discovery, frontmatter parsing, prompt projection, and the `skill` tool 3a110e3
- [x] Task: Implement `src/skills.py` with `SkillInfo`, `discover_skills()`, `render_skills_prompt()`, and `execute_skill_tool()` 3a110e3
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) 3a110e3

### Phase 2: Stdio MCP Client & Server Manager (`src/mcp.py`) [checkpoint: a88c1c6]
- [x] Task: Write unit tests in `tests/test_mcp.py` testing JSON-RPC 2.0 handshake, `tools/list` schema extraction, and `tools/call` dispatch a88c1c6
- [x] Task: Implement stdio JSON-RPC MCP client and server manager in `src/mcp.py` using Python standard library a88c1c6
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) a88c1c6

### Phase 3: Unification with ToolRegistry & AgentLoop [checkpoint: 6c9ab6e]
- [x] Task: Write integration tests in `tests/test_mcp_skills_integration.py` verifying AgentLoop with internal, skill, and MCP tools 6c9ab6e
- [x] Task: Integrate Skills and MCP servers into `ToolRegistry` in `src/executor.py` and `AgentLoop` in `src/agent.py` 6c9ab6e
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) 6c9ab6e

### Phase 4: Full System Verification & End-to-End Regression [checkpoint: 6c9ab6e]
- [x] Task: Run full test suite (`pytest`), verify clean `pre-commit` across all files, and verify live execution 6c9ab6e
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) 6c9ab6e
