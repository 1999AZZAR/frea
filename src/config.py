"""User configuration management in ~/.config/frea/ conforming to OpenCode schema."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

DEFAULT_CONFIG: Dict[str, Any] = {
    "$schema": "https://frea.ai/config.json",
    "model": "openrouter/auto",
    "fallback_model": "openrouter/free",
    "provider": "openrouter",
    "auto_approve": False,
    "permission": {
        "read": "allow",
        "grep": "allow",
        "find": "allow",
    },
}

DEFAULT_TUI_CONFIG: Dict[str, Any] = {
    "$schema": "https://frea.ai/tui.json",
    "theme": "opencode",
}


def get_config_dir() -> Path:
    """Return ~/.config/frea, respecting XDG_CONFIG_HOME."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "frea"
    return Path.home() / ".config" / "frea"


def ensure_config_scaffold(
    config_dir: Optional[Path] = None,
) -> Tuple[Path, Path]:
    """Ensure ~/.config/frea directory, default json files, and subfolders exist."""
    target_dir = config_dir or get_config_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    config_path = target_dir / "config.json"
    if not config_path.exists():
        config_path.write_text(json.dumps(DEFAULT_CONFIG, indent=2))

    tui_path = target_dir / "tui.json"
    if not tui_path.exists():
        tui_path.write_text(json.dumps(DEFAULT_TUI_CONFIG, indent=2))

    (target_dir / "logs").mkdir(exist_ok=True)
    (target_dir / "exports").mkdir(exist_ok=True)

    persona_dir = target_dir / "persona"
    if not persona_dir.exists():
        canonical = Path("/home/azzar/agent_persona")
        if canonical.exists():
            try:
                persona_dir.symlink_to(canonical, target_is_directory=True)
            except OSError:
                persona_dir.mkdir(exist_ok=True)
        else:
            persona_dir.mkdir(exist_ok=True)

    return config_path, tui_path


def load_frea_config(
    custom_path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """Load configuration from custom path or ~/.config/frea/config.json."""
    if custom_path:
        p = Path(custom_path)
    else:
        cfg_path, _ = ensure_config_scaffold()
        p = cfg_path

    if not p.exists():
        return dict(DEFAULT_CONFIG)

    try:
        data = json.loads(p.read_text())
        merged = dict(DEFAULT_CONFIG)
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_CONFIG)


def save_frea_config(
    config_data: Dict[str, Any],
    custom_path: Optional[str | Path] = None,
) -> None:
    """Save configuration to custom path or ~/.config/frea/config.json."""
    if custom_path:
        p = Path(custom_path)
    else:
        cfg_path, _ = ensure_config_scaffold()
        p = cfg_path

    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(config_data, indent=2))


def load_tui_config(
    custom_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Load tui.json configuration."""
    target_dir = custom_dir or get_config_dir()
    tui_path = target_dir / "tui.json"
    if not tui_path.exists():
        ensure_config_scaffold(target_dir)

    try:
        data = json.loads(tui_path.read_text())
        merged = dict(DEFAULT_TUI_CONFIG)
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_TUI_CONFIG)
