# Track Specification: Bake Persona from `/home/azzar/agent_persona` & Migrate `src/config` to `~/.config/frea`

## Overview
Bake Frea's canonical persona (`IDENTITY.md`, `SOUL.md`, `USER.md`, `RTK.md`, `AGENTS.md`) located in `/home/azzar/agent_persona` directly into the agent harness's core reasoning loops (`AgentLoop`, `AIChat`, `ChatInitializer`).
Replace all usage of `/home/azzar/project/TUI_Agent/frea/src/config` by redirecting legacy configuration, instructions, logs, and exports to `~/.config/frea/` (respecting `$XDG_CONFIG_HOME`), and purge the obsolete `src/config/` directory from the repository.

## Functional Requirements
1. **Persona Resolution & Assembly (`src/persona.py`)**:
   - Provide `load_frea_persona(persona_dir: Optional[Path] = None) -> str`.
   - Resolution order: `FREA_PERSONA_DIR` env var -> `/home/azzar/agent_persona` -> `~/.config/frea/persona` -> embedded resilient fallback string.
   - Assembles identity, soul, user context, token killer protocol, and behavioral guidelines into a unified system prompt.
   - Scaffold persona link or copy in `~/.config/frea/persona` via `ensure_config_scaffold()`.
2. **System Prompt Integration**:
   - Update `DEFAULT_SYSTEM_PROMPT` in `src/agent.py` to use `load_frea_persona()`.
   - Update `AIChat` in `src/main.py` and `ChatInitializer` in `src/chat_initializer.py` to default to `load_frea_persona()`.
3. **Legacy Path Migration to `~/.config/frea`**:
   - Update `ChatConfig` in `src/chat_config.py` to source `CONFIG_FILE`, `DEFAULT_INSTRUCTION_FILE`, `LOG_FOLDER`, and `EXPORT_FOLDER` from `get_config_dir()` (`~/.config/frea/`).
4. **Purge `src/config/`**:
   - Remove `/home/azzar/project/TUI_Agent/frea/src/config/` directory from the repository.
   - Update `.gitignore` to remove references to `src/config/`.

## Non-Functional Requirements
- **Security-First**: Never expose private API keys or tokens in prompt files or configuration scaffolds.
- **YAGNI & Lean Design**: Minimal clean implementation conforming to Caveman Protocol.
- **Resilience**: Agent operates cleanly even if `/home/azzar/agent_persona` is unmounted or moved, using high-fidelity embedded fallback.

## Acceptance Criteria
- [ ] `load_frea_persona()` successfully loads and assembles persona files when `/home/azzar/agent_persona` exists.
- [ ] Embedded fallback works when persona directory is absent.
- [ ] `AgentLoop`, `AIChat`, and `ChatInitializer` incorporate Frea's persona in system prompts.
- [ ] `src/config/` directory is completely removed from the project root.
- [ ] `ChatConfig` stores configuration, logs, and exports in `~/.config/frea/`.
- [ ] 100% of test suite passes across `.venv` and system Python.
- [ ] All pre-commit hooks pass.
