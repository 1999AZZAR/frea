# Plan: OpenCode 1:1 TUI Overhaul and Wiring

- [x] **Phase 1: OpenCode Glyph Logo & Theme System**
  - [x] Implement OpenCode `tint()` background shading helper and character mapping (`_`, `^`, `~`, `,`, `█`, `▀`, `▄`) in `src/ui.py`.
  - [x] Update `src/ui.py` with OpenCode `FREA` logo definition and palette constants matching `opencode.json`.
  - [x] Update tests in `tests/test_theme.py`.

- [x] **Phase 2: 1:1 OpenCode Statusline & `/status` Dialog**
  - [x] Update `render_statusline` in `src/ui.py` and `src/tui.py` with real MCP count and directory formatting.
  - [x] Enhance `handle_slash_command` in `src/commands.py` to render OpenCode-style rich status dialog with MCP connection status and skills list.
  - [x] Update tests in `tests/test_commands.py` and `tests/test_tui_opencode.py`.

- [x] **Phase 3: 1:1 Inline Tool Cards & Agent Loop Integration**
  - [x] Refactor `src/cards.py` to support new standard tools (`read_file`, `write_file`, `patch_file`, `grep`, `glob`, `run_command`, `skill`, `update_plan`, and MCP tools) with OpenCode icons (`$`, `←`, `→`, `✱`, `⚙`), diff cards, and collapsed outputs.
  - [x] Wire live card rendering into `src/agent.py` and `src/tui.py` so tool execution streams visually in real time.
  - [x] Update tests in `tests/test_cards.py` and `tests/test_tui_opencode.py`.

- [x] **Phase 4: Verification & Pre-commit Checkpoint**
  - [x] Run test suite with `rtk pytest`.
  - [x] Run `rtk pre-commit run --all-files`.
  - [x] Verify `./src/frea` execution and update Conductor track status.
