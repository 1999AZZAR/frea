# Specification: OpenCode 1:1 TUI Overhaul and Wiring

## Problem Statement
Frea requires a 1:1 visual and interactive terminal experience identical to OpenCode (`/home/azzar/project/TUI_Agent/opencode`), including:
1. Block typography logo rendering with character mapping (`_`, `^`, `~`, `,`, `█`, `▀`, `▄`), tinted shadow backgrounds, and dual-tone layout (muted left half, bold primary right half).
2. Color theme palette matching OpenCode's `opencode.json` (`#fab283` primary, `#5c9cf5` secondary, `#141414` background panel, `#0a0a0a` background, diff colors, syntax colors).
3. 1:1 Bottom statusline: `<dir>    [△ permissions]  • {count} Tools  ⊙ {count} MCP  /status`.
4. Interactive `/status` command dialog displaying session metadata, active model, provider, connected MCP servers with status indicators, and loaded tools/skills.
5. Rich inline tool execution cards (`InlineToolRow`) showing pending states (`~ {pending}`), completed tool calls with icons (`$`, `←`, `→`, `✱`, `⚙`), syntax-highlighted unified diffs, collapsible stdout/stderr outputs, and execution timing.
6. Seamless wiring into `src/tui.py`, `src/cards.py`, `src/commands.py`, `src/ui.py`, and `src/main.py` ensuring both non-interactive (batch) and interactive REPL modes work flawlessly.

## Acceptance Criteria
- [ ] Block logo renderer correctly parses glyphs `_^~,█▀▄` into tinted terminal cells matching OpenCode's typography.
- [ ] Theme constants match OpenCode `defs` and semantic color roles.
- [ ] Bottom statusline dynamically displays real directory, tool counts, active MCP server connections (`⊙ {n} MCP`), and `/status`.
- [ ] `/status` slash command prints a clean OpenCode-style modal card with MCP server status and session info.
- [ ] Inline tool calls in `src/cards.py` support both new (`read_file`, `write_file`, `patch_file`, `grep`, `glob`, `run_command`, `skill`, MCP tools) and legacy tool names with OpenCode icons and diff formatting.
- [ ] All 108 existing tests pass, plus new tests covering the updated 1:1 UI, logo, cards, and status command.
- [ ] Pre-commit hooks pass.
