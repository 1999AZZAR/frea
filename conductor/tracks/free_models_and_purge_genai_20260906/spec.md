# Track Specification: Add OpenCode & KiloCode Free Models & Purge Gemini/GenAI Dependency

## Overview
Enable immediate, keyless, out-of-the-box execution for Frea by incorporating the free model gateways used internally by OpenCode (`https://api.opencode.ai/v1`) and KiloCode (`https://api.kilo.ai/api/gateway`).
Completely purge the deprecated `google-generativeai` SDK from all dependencies, environments, and source files, migrating any legacy Gemini access to standard OpenAI-compatible endpoints.

## Functional Requirements
1. **Purge `google-generativeai`**:
   - Remove `google-generativeai>=0.8.0` from `requirements.txt` (leaving exactly 3 production dependencies: `openai`, `rich`, `prompt_toolkit`).
   - Uninstall `google-generativeai` from `.venv`.
   - Remove `import google.generativeai as genai` from `src/chat_config.py` and replace with zero-dependency handling.
   - Update `tests/test_clean_requirements.py` to enforce the 3-package constraint.
2. **OpenCode & KiloCode Free Providers (`src/providers.py`)**:
   - `OpencodeProvider(OpenAIProvider)`:
     - Base URL: `https://api.opencode.ai/v1`
     - Default headers: `{"HTTP-Referer": "https://opencode.ai/", "X-Title": "opencode"}`
     - Default API key: `"public"` (keyless)
     - Supported free models: `kimi-k2.5-free`, `deepseek-v4-flash:free`, `glm-4.7-flash-free`, `opencode/free`
   - `KiloCodeProvider(OpenAIProvider)`:
     - Base URL: `https://api.kilo.ai/api/gateway`
     - Default headers: `{"HTTP-Referer": "https://opencode.ai/", "X-Title": "opencode"}`
     - Default API key: `"public"` or `KILOCODE_API_KEY`
     - Supported free models: `kilocode/kilo-auto/balanced`, `kilo-auto`, `kilo/free`
   - `GeminiProvider`:
     - Refactored to subclass `OpenAIProvider` targeting `https://generativelanguage.googleapis.com/v1beta/openai/`, without any `google-generativeai` dependency.
   - `get_provider()`:
     - Recognize `opencode`, `kilo`, `kilocode`, `openrouter`, `groq`, `openai`, `gemini`.
     - When no API keys or models are configured, smoothly route to keyless free models so commands run out-of-the-box.
3. **Configuration Defaults (`src/config.py`)**:
   - Support `opencode` or `openrouter` with free model defaults in `DEFAULT_CONFIG`.

## Non-Functional Requirements
- Zero external credentials required for initial CLI execution.
- Clean pre-commit gates.
- 100% test pass rate across `.venv` and Python 3.

## Acceptance Criteria
- [ ] `google-generativeai` is completely removed from `requirements.txt` and `.venv`.
- [ ] No `google-generativeai` imports exist in any project file.
- [ ] `OpencodeProvider` and `KiloCodeProvider` can be instantiated without an API key.
- [ ] `get_provider("opencode")` and `get_provider("kilo")` return working provider instances.
- [ ] All 70+ automated tests pass cleanly.
