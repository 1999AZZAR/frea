# Implementation Plan: Bake Persona & Migrate `src/config` to `~/.config/frea`

### Phase 1: Persona Loader & Assembly Engine [checkpoint: dad2d6d]
- [x] Task: Write unit tests for persona resolution, file assembly, and embedded fallback in `tests/test_persona.py` 7a1434f
- [x] Task: Implement `src/persona.py` loading `/home/azzar/agent_persona` with embedded backup dad2d6d
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) dad2d6d

### Phase 2: Agent System Prompt Integration [checkpoint: ab9a313]
- [x] Task: Write tests for persona injection into `AgentLoop`, `AIChat`, and `ChatInitializer` in `tests/test_agent_persona.py` 3690da0
- [x] Task: Wire assembled persona into `src/agent.py`, `src/main.py`, and `src/chat_initializer.py` ab9a313
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) ab9a313

### Phase 3: Purge `src/config/` & Migrate Legacy Paths to `~/.config/frea`
- [ ] Task: Update `src/chat_config.py` and `src/config.py` to root all logs, exports, and config paths in `~/.config/frea`
- [ ] Task: Remove `/home/azzar/project/TUI_Agent/frea/src/config/` directory and update `.gitignore`
- [ ] Task: Run full test suite, verify clean pre-commit hooks, and verify live scaffolding
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
