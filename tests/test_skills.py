from pathlib import Path
from src.skills import (
    SkillInfo,
    discover_skills,
    load_skill,
    parse_skill_md,
    render_skills_prompt,
)


def test_parse_skill_md(tmp_path: Path):
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        """---
name: test-skill
description: A helpful test skill for unit tests
---
# Test Skill Instructions
Follow these steps carefully:
1. Do this
2. Do that
""",
        encoding="utf-8",
    )
    (skill_dir / "helper.py").write_text("print('helper')")

    info = parse_skill_md(skill_md)
    assert info is not None
    assert info.name == "test-skill"
    assert info.description == "A helpful test skill for unit tests"
    assert "Test Skill Instructions" in info.content
    assert "helper.py" in info.files


def test_discover_skills(tmp_path: Path):
    skills_root = tmp_path / "skills"
    skills_root.mkdir()

    # Skill 1
    s1 = skills_root / "skill-alpha"
    s1.mkdir()
    (s1 / "SKILL.md").write_text(
        "---\nname: skill-alpha\ndescription: Alpha skill\n---\nBody Alpha",
        encoding="utf-8",
    )

    # Skill 2
    s2 = skills_root / "skill-beta"
    s2.mkdir()
    (s2 / "SKILL.md").write_text(
        "---\nname: skill-beta\ndescription: Beta skill\n---\nBody Beta",
        encoding="utf-8",
    )

    discovered = discover_skills(search_paths=[skills_root])
    assert "skill-alpha" in discovered
    assert "skill-beta" in discovered
    assert discovered["skill-alpha"].description == "Alpha skill"


def test_render_skills_prompt():
    skills = {
        "alpha": SkillInfo(
            name="alpha",
            description="Alpha description",
            location=Path("/tmp/alpha/SKILL.md"),
            content="Alpha content",
            files=[],
        )
    }
    prompt = render_skills_prompt(skills)
    assert "<skills>" in prompt
    assert "- alpha: Alpha description" in prompt
    assert "</skills>" in prompt


def test_load_skill_tool(tmp_path: Path):
    skill_dir = tmp_path / "deploy-tool"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: deploy-tool\ndescription: Deployment guidelines\n---\nRun deploy.sh",
        encoding="utf-8",
    )
    (skill_dir / "deploy.sh").write_text("echo deploying")

    skills = discover_skills(search_paths=[tmp_path])
    res = load_skill("deploy-tool", skills=skills)
    assert res.success is True
    assert '<skill_content name="deploy-tool">' in res.output
    assert "Run deploy.sh" in res.output
    assert "<file>deploy.sh</file>" in res.output

    # Nonexistent skill
    res_missing = load_skill("nonexistent", skills=skills)
    assert res_missing.success is False
    assert "not found" in res_missing.error.lower()
