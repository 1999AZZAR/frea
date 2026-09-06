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


def test_cli_config_integration(tmp_path):
    import json
    from src.cli import parse_args

    cfg_file = tmp_path / "custom.json"
    cfg_file.write_text(
        json.dumps({"model": "anthropic/claude-3-haiku", "auto_approve": True})
    )

    cli_cfg = parse_args(["-c", str(cfg_file)])
    frea_cfg = load_frea_config(cli_cfg.config_path)
    assert frea_cfg["model"] == "anthropic/claude-3-haiku"
    assert frea_cfg["auto_approve"] is True

    cli_cfg_override = parse_args(["-c", str(cfg_file), "-m", "groq/llama-3.3-70b"])
    effective_model = cli_cfg_override.model or frea_cfg.get("model")
    assert effective_model == "groq/llama-3.3-70b"
