from src.config import (
    ensure_config_scaffold,
    get_config_dir,
    load_frea_config,
    load_tui_config,
    save_frea_config,
)


def test_get_config_dir_custom_xdg(tmp_path, monkeypatch):
    custom_xdg = tmp_path / "custom_config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(custom_xdg))
    cfg_dir = get_config_dir()
    assert cfg_dir == custom_xdg / "frea"


def test_ensure_config_scaffold(tmp_path):
    cfg_path, tui_path = ensure_config_scaffold(tmp_path)
    assert cfg_path.exists()
    assert tui_path.exists()

    cfg_data = load_frea_config(cfg_path)
    assert cfg_data["model"] == "openrouter/auto"
    assert cfg_data["provider"] == "openrouter"
    assert cfg_data["permission"]["read"] == "allow"

    tui_data = load_tui_config(tmp_path)
    assert tui_data["theme"] == "opencode"


def test_save_and_load_frea_config(tmp_path):
    cfg_path, _ = ensure_config_scaffold(tmp_path)
    cfg_data = load_frea_config(cfg_path)
    cfg_data["model"] = "anthropic/claude-3.7-sonnet"
    save_frea_config(cfg_data, cfg_path)

    reloaded = load_frea_config(cfg_path)
    assert reloaded["model"] == "anthropic/claude-3.7-sonnet"
