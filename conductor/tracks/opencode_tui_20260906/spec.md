# Specification: OpenCode TUI Overhaul, Dependency Cleanup & `.venv` Integration

## 1. Overview
Modernize Frea's terminal interface to faithfully replicate OpenCode TUI (`/home/azzar/project/TUI_Agent/opencode`), purge obsolete LangChain dependencies, and wire the local `.venv` environment for development and testing.

---

## 2. Functional Requirements
- **Dependency & Environment Cleanup**:
  - Remove `langchain` and related packages from `requirements.txt`.
  - Clean up `.venv` by uninstalling `langchain` packages and ensuring `rich`, `prompt_toolkit`, and `pytest` are installed.
- **OpenCode Visual Header & Logo**:
  - OpenCode dual-tone block logo for `FREA` (muted shadow + highlighted foreground blocks) matching `opencode/packages/tui/src/logo.ts`.
  - Session header displaying active model tag (`openrouter/auto`), provider, and session info.
- **OpenCode Tool Call Cards**:
  - Shell: `$ <command>` with inline spinner and collapsible output block.
  - File Read: `→ Read <filepath>` with `↳ Loaded` sub-lines.
  - File Write: `← Write <filepath>` with path badge.
  - File Patch / Edit: `← Patched <filepath>` with syntax-highlighted unified diffs (green `+`, red `-`, line numbers).
  - Search / Glob: `✱ Grep` and `✱ Glob` cards with count badges `(N matches)`.
- **OpenCode Statusline Footer**:
  - Left: Formatted working directory path (e.g., `~/project/TUI_Agent/frea`).
  - Right: `• Model: openrouter/auto` | `⊙ 6 Tools` | `/help` hint.
- **Interactive Prompt & Command Palette**:
  - `prompt_toolkit` input with OpenCode prompt symbol (`❯ `), history navigation, and slash command autocompletion (`/help`, `/model`, `/compact`, `/status`, `/clear`, `/exit`).
- **Permission Prompt**:
  - OpenCode-styled permission prompt: `△ Permission needed: Run <tool> '<target>'? [y/N]`.

---

## 3. Non-Functional Requirements
- Minimal token overhead and sub-millisecond local rendering.
- Resilient terminal behavior (graceful fallback if terminal does not support 256 colors or when running non-interactively).
- 100% test coverage with automated unit tests for TUI rendering, commands, and dependency checks.
- Adherence to Caveman protocol, RTK command execution, and clean pre-commit hooks.

---

## 4. Acceptance Criteria
- [ ] LangChain is completely purged from `requirements.txt` and `.venv`.
- [ ] `.venv` runs `pytest` successfully.
- [ ] TUI renders OpenCode block logo, tool cards, colored diffs, and bottom statusline.
- [ ] All slash commands work with interactive autocompletion and help cards.
- [ ] Headless batch execution (`-p`) continues to work flawlessly.
- [ ] All tests pass in `pytest`, and all pre-commit hooks pass.
