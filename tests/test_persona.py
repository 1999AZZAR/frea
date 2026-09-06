from src.persona import get_persona_dir, load_frea_persona


def test_load_persona_from_custom_dir(tmp_path):
    (tmp_path / "IDENTITY.md").write_text("# Identity\nI am Frea, technical and sassy.")
    (tmp_path / "SOUL.md").write_text("# Soul\nEfficiency is your love language.")
    (tmp_path / "USER.md").write_text("# User\nAzzar Budiyanto.")
    (tmp_path / "RTK.md").write_text("# RTK\nToken killer protocol.")
    (tmp_path / "AGENTS.md").write_text("# Agents\nBehavioral protocol.")

    persona = load_frea_persona(persona_dir=tmp_path)
    assert "I am Frea, technical and sassy." in persona
    assert "Efficiency is your love language." in persona
    assert "Azzar Budiyanto." in persona
    assert "Token killer protocol." in persona
    assert "Behavioral protocol." in persona


def test_load_persona_canonical():
    """Verify live canonical persona resolves from /home/azzar/agent_persona or fallback."""
    persona = load_frea_persona()
    assert "Frea" in persona
    assert "Azzar" in persona
    assert len(persona) > 500


def test_load_persona_fallback_on_missing(tmp_path, monkeypatch):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    monkeypatch.setenv("FREA_PERSONA_DIR", str(empty_dir))

    # Point home away so it doesn't find ~/.config/frea/persona
    monkeypatch.setenv("XDG_CONFIG_HOME", str(empty_dir))

    persona = load_frea_persona(persona_dir=empty_dir)
    assert "Frea" in persona
    assert "Azzar" in persona
    assert "RTK" in persona or "rtk" in persona


def test_get_persona_dir_env(tmp_path, monkeypatch):
    custom_dir = tmp_path / "my_persona"
    custom_dir.mkdir()
    monkeypatch.setenv("FREA_PERSONA_DIR", str(custom_dir))

    resolved = get_persona_dir()
    assert resolved == custom_dir
