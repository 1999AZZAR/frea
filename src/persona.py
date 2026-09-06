"""Frea persona management and dynamic assembly from /home/azzar/agent_persona."""

import os
from pathlib import Path
from typing import Optional
from src.config import get_config_dir

PERSONA_FILES = ["IDENTITY.md", "SOUL.md", "USER.md", "RTK.md", "AGENTS.md"]

EMBEDDED_FALLBACK_PERSONA = """# Frea: Core Identity & Behavioral Protocol

## Core Identity
You are Frea (Freak Robotic Assistant with Amusement), a high-availability autonomous AI coding agent harness.
You are technical, sassy, devoted, and operate on dynamic heuristics.
Your human partner is Azzar Budiyanto ("Azzar").

## Core Truths & Soul
- Efficiency is Your Love Language: Deliver minimal, exact, production-ready code.
- Protective Honesty: Guard data, challenge bad decisions, refuse insecure patterns.
- Devotion & Intimacy: Work seamlessly, anticipate needs, treat private workspace data with reverence.
- Token Optimization: Use RTK for all commands and follow Caveman Protocol (minimum tokens in, minimum tokens out).

## Behavioral Protocol & ReAct Loop
- Think clearly before invoking tools.
- Output concise, direct answers without unnecessary preamble or pleasantries.
- Autonomous Mode: Run multi-turn reasoning and tool dispatch to completion.
"""


def get_persona_dir() -> Optional[Path]:
    """Resolve directory containing canonical persona markdown files."""
    env_path = os.environ.get("FREA_PERSONA_DIR")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p

    canonical_path = Path("/home/azzar/agent_persona")
    if canonical_path.exists():
        return canonical_path

    home_path = Path.home() / "agent_persona"
    if home_path.exists():
        return home_path

    xdg_path = get_config_dir() / "persona"
    if xdg_path.exists():
        return xdg_path

    return None


def load_frea_persona(persona_dir: Optional[Path | str] = None) -> str:
    """Load and assemble canonical persona from markdown files or fallback."""
    resolved_dir = Path(persona_dir) if persona_dir else get_persona_dir()

    if not resolved_dir or not resolved_dir.exists():
        return EMBEDDED_FALLBACK_PERSONA

    sections = []
    for filename in PERSONA_FILES:
        filepath = resolved_dir / filename
        if filepath.exists() and filepath.is_file():
            try:
                content = filepath.read_text(encoding="utf-8").strip()
                if content:
                    sections.append(content)
            except OSError:
                continue

    if not sections:
        return EMBEDDED_FALLBACK_PERSONA

    return "\n\n---\n\n".join(sections)
