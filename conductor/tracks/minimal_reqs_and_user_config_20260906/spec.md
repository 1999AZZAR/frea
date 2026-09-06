# Specification: Minimal Requirements & `~/.config/frea/` User Configuration

## 1. Overview
Remake `requirements.txt` to list strictly essential production packages (`openai`, `google-generativeai`, `rich`, `prompt_toolkit`), purge unused packages (`emoji`, `fpdf2`, `wikipedia-api`), and implement an OpenCode-identical configuration system storing `config.json` and `tui.json` in `~/.config/frea/`.

---

## 2. Functional Requirements
- **Requirements Streamlining**:
  - `requirements.txt`: Keep only `openai`, `google-generativeai`, `rich`, `prompt_toolkit`.
  - `requirements-dev.txt`: Include `pytest`, `pytest-asyncio`.
  - Uninstall `emoji`, `fpdf2`, `wikipedia-api` from `.venv`.
  - Ensure `src/agent_tools.py` and `src/chat_initializer.py` gracefully handle absence of `wikipediaapi` with lazy imports.
- **XDG User Configuration (`~/.config/frea/`)**:
  - Create `src/config.py` resolving `~/.config/frea/` (respecting `$XDG_CONFIG_HOME`).
  - Auto-scaffold `config.json` with OpenRouter defaults (`openrouter/auto`, fallback `openrouter/free`, permissions).
  - Auto-scaffold `tui.json` with theme configuration (`"theme": "opencode"`).
  - Connect `src/cli.py` (`--config` flag) and `src/main.py` to read settings from `~/.config/frea/config.json`.
- **Testing & Verification**:
  - Test suite verifying minimal dependencies and config loading/saving in `~/.config/frea/`.
  - 100% tests passing in `.venv` and system python.

---

## 3. Non-Functional Requirements
- Strictly zero unwanted dependencies installed or referenced.
- Safe creation of directories in user space with POSIX `0o700` permission if needed.
- Graceful degradation if user configuration directory cannot be written.
- Full compliance with Caveman protocol and pre-commit hooks.
