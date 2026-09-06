# Implementation Plan: OpenCode & KiloCode Free Models & Purge GenAI Dependency

### Phase 1: Purge `google-generativeai` Dependency [checkpoint: 12da4e1]
- [x] Task: Update `tests/test_clean_requirements.py` to assert only 3 production dependencies (`openai`, `rich`, `prompt_toolkit`) 36eaf52
- [x] Task: Remove `google-generativeai` from `requirements.txt`, purge from `.venv`, and remove import from `src/chat_config.py` 12da4e1
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) 12da4e1

### Phase 2: OpenCode & KiloCode Free Providers
- [ ] Task: Write unit tests for `OpencodeProvider`, `KiloCodeProvider`, and OpenAI-compatible `GeminiProvider` in `tests/test_free_providers.py`
- [ ] Task: Implement `OpencodeProvider`, `KiloCodeProvider`, and refactor `GeminiProvider` in `src/providers.py`
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

### Phase 3: Zero-Config Defaults & End-to-End Verification
- [ ] Task: Update `src/config.py` defaults and verify keyless instantiation across CLI & AgentLoop
- [ ] Task: Run full test suite, verify clean pre-commit hooks, and verify live keyless execution
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
