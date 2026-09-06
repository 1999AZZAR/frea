# Implementation Plan: Minimal Requirements & `~/.config/frea/` User Configuration

### Phase 1: Streamline Requirements & Dependency Hygiene [checkpoint: d1a18e2]
- [x] Task: Write tests verifying minimal requirements and lazy import safety in `tests/test_clean_requirements.py` cd4a788
- [x] Task: Remake `requirements.txt`, create `requirements-dev.txt`, purge unused packages from `.venv`, make `agent_tools.py` lazy-load wikipediaapi d1a18e2
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) d1a18e2

### Phase 2: User Configuration Engine (`~/.config/frea/`)
- [x] Task: Write unit tests for XDG config resolution, scaffolding, and validation in `tests/test_user_config.py` 0f834d1
- [~] Task: Implement `src/config.py` managing `~/.config/frea/config.json` and `~/.config/frea/tui.json`
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

### Phase 3: CLI Integration & End-to-End Verification
- [ ] Task: Wire `src/cli.py` and `src/main.py` to default to `~/.config/frea/config.json` with CLI `--config` override
- [ ] Task: Run full test suite, verify clean pre-commit hooks, and verify live scaffolding
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
