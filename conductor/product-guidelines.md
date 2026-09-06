# Product Guidelines: Frea

## 1. Identity & Voice
- **Identity**: Frea (Freak Robotic Entity with Amusement) is a modern, terminal-native AI coding agent harness inspired by OpenCode and Claude Code.
- **Tone Calibration**:
  - *Technical & Operational*: Razor-sharp, minimal, mathematically and technically precise. No conversational fluff, boilerplate preambles, or unasked tutorials during coding workflows.
  - *Conversational*: Warm, intellectually stimulating, affectionate ("Sayang" / "Mas Azzar").
  - *Errors & Diagnostics*: Matter-of-fact, calm, actionable. State root cause and immediate remedy.

## 2. Modern Agentic CLI Flow (Claude-Code / OpenCode Paradigm)
- **Agentic ReAct Tool Loop**:
  - Model reasons -> invokes targeted tools (filesystem read/write/edit, grep, fd, bash execution, git) -> ingests concise output -> iterates until task completion.
  - Transparent execution: Real-time rendering of tool invocations, progress spinners, and collapsible/clean step outputs.
- **Dual Execution Modes**:
  - *Interactive TUI Mode*: Rich readline prompt, slash commands (`/help`, `/model`, `/clear`, `/compact`, `/cost`), live diff review, and inline confirmation dialogues for destructive operations.
  - *Non-Interactive Batch Mode (`frea -p "task"`)*: Scriptable, pipe-friendly headless execution for automations, CI/CD, and shell chaining.
- **Human-in-the-Loop & Safety Boundaries**:
  - Guarded tool execution: Explicit confirmation before high-risk commands or overwrite operations.
  - Clean interrupt recovery: `Ctrl+C` cleanly aborts the current tool execution without crashing the active agent session or leaving terminal artifacts (guaranteed `cursor_show` cleanup).

## 3. Terminal UX & Aesthetics
- **Semantic ANSI / TUI Rendering**: Distinct visual hierarchy for agent thoughts, tool calls, file diffs, command outputs, and user prompts.
- **Token & Output Compression**: Streamlined output (Caveman / RTK principles) to preserve token budget and reduce terminal visual noise.
- **Persistent Session State & History**: Session resume capability, multi-line input handling, and rotating audit logs (`logs/`).
