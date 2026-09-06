# Implementation Plan: OpenCode TUI Overhaul, Dependency Cleanup & `.venv` Integration

### Phase 1: Environment & Dependency Hygiene [checkpoint: 5e0fcf7]
- [x] Task: Write tests verifying absence of LangChain imports and verifying environment requirements in `tests/test_dependencies.py` b7b2b82
- [x] Task: Purge LangChain from `requirements.txt` and `.venv`, add `rich` and `prompt_toolkit` to requirements 5e0fcf7
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) 5e0fcf7

### Phase 2: OpenCode Theme, Block Logo & Header
- [x] Task: Write tests for OpenCode block logo rendering, model banner, and theme palette in `tests/test_theme.py` 831bcf1
- [x] Task: Implement OpenCode dual-tone block logo and session banner in `src/ui.py` 44a6b7a
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

### Phase 3: OpenCode Tool Cards & Syntax Diffs
- [ ] Task: Write tests for OpenCode tool card formatting (`$`, `→`, `←`, `✱`) and unified diff renderer in `tests/test_tool_cards.py`
- [ ] Task: Implement tool card renderers with inline/block states, output collapse, and colored diff badges
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

### Phase 4: OpenCode Statusline, Prompt & Slash Palette
- [ ] Task: Write tests for OpenCode statusline footer, prompt_toolkit autocompletion, and slash command palette in `tests/test_tui_opencode.py`
- [ ] Task: Implement OpenCode bottom statusline (`directory`, `model`, `tools`), `prompt_toolkit` interactive prompt (`❯ `), and command palette
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

### Phase 5: End-to-End Integration & Final Polish
- [ ] Task: Write full integration tests covering interactive REPL turns, batch mode (`-p`), and OpenCode permission alerts
- [ ] Task: Verify 100% test pass rate across system python and `.venv`, verify pre-commit hooks
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
