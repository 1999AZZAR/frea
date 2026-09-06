"""Skills discovery, prompt injection, and execution engine (OpenCode parity)."""

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
from typing import Dict, List, Optional
from src.tools import ToolResult

MAX_SAMPLE_FILES = 10


@dataclass
class SkillInfo:
    """Metadata and content for an individual skill."""

    name: str
    description: str
    location: Path
    content: str
    files: List[str] = field(default_factory=list)


def parse_frontmatter(text: str) -> Dict[str, str]:
    """Extract key-value pairs from simple YAML frontmatter without external yaml library."""
    data: Dict[str, str] = {}
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return data

    frontmatter_block = match.group(1)
    for line in frontmatter_block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip().lower()] = val.strip().strip("'\"")
    return data


def parse_skill_md(file_path: Path) -> Optional[SkillInfo]:
    """Parse a SKILL.md file into SkillInfo."""
    try:
        raw_text = file_path.read_text(encoding="utf-8", errors="replace")
        meta = parse_frontmatter(raw_text)

        # Name defaults to directory name if not in frontmatter
        name = meta.get("name") or file_path.parent.name
        description = meta.get("description") or "Specialized skill"

        # Content is body after frontmatter
        body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", raw_text, flags=re.DOTALL).strip()

        # Sample other files in skill directory
        skill_dir = file_path.parent
        files = []
        for p in sorted(skill_dir.rglob("*")):
            if p.is_file() and p.name != "SKILL.md":
                rel = p.relative_to(skill_dir).as_posix()
                files.append(rel)
                if len(files) >= MAX_SAMPLE_FILES:
                    break

        return SkillInfo(
            name=name,
            description=description,
            location=file_path,
            content=body,
            files=files,
        )
    except Exception:
        return None


def get_default_skill_directories() -> List[Path]:
    """Standard skill search paths in descending priority."""
    paths = []
    # 1. Project local skills
    paths.append(Path(".agents/skills"))
    paths.append(Path(".opencode/skills"))
    # 2. User config skills
    xdg = os.environ.get("XDG_CONFIG_HOME")
    config_dir = Path(xdg) / "frea" if xdg else Path.home() / ".config" / "frea"
    paths.append(config_dir / "skills")
    # 3. Global user skills
    paths.append(Path.home() / ".agents" / "skills")
    paths.append(Path.home() / ".opencode" / "skills")
    return paths


def discover_skills(
    search_paths: Optional[List[Path]] = None,
) -> Dict[str, SkillInfo]:
    """Discover all available skills across search paths."""
    directories = (
        search_paths if search_paths is not None else get_default_skill_directories()
    )
    skills: Dict[str, SkillInfo] = {}

    for base_dir in directories:
        if not base_dir.is_dir():
            continue

        # Look for directories containing SKILL.md
        for child in base_dir.iterdir():
            if child.is_dir():
                skill_md = child / "SKILL.md"
                if skill_md.is_file():
                    info = parse_skill_md(skill_md)
                    if info and info.name not in skills:
                        skills[info.name] = info

    return skills


def render_skills_prompt(skills: Dict[str, SkillInfo]) -> str:
    """Format skills catalog for system prompt injection."""
    if not skills:
        return ""

    lines = [
        "<skills>",
        "You can load specialized skills using the `skill` tool when relevant to the task:",
    ]
    for name, info in sorted(skills.items()):
        lines.append(f"- {name}: {info.description}")
    lines.append("</skills>")
    return "\n".join(lines)


def load_skill(name: str, skills: Optional[Dict[str, SkillInfo]] = None) -> ToolResult:
    """Execute the skill tool to inject skill instructions and files into context."""
    active_skills = skills if skills is not None else discover_skills()
    skill = active_skills.get(name)

    if not skill:
        available = ", ".join(sorted(active_skills.keys())) if active_skills else "none"
        return ToolResult(
            success=False,
            error=f"Skill '{name}' not found. Available skills: {available}",
        )

    directory = skill.location.parent.resolve().as_posix()
    file_tags = "\n".join(f"<file>{f}</file>" for f in skill.files)

    output = f"""<skill_content name="{skill.name}">
# Skill: {skill.name}

{skill.content}

Base directory for this skill: {directory}
Relative paths in this skill (e.g., scripts/, reference/) are relative to this base directory.

<skill_files>
{file_tags}
</skill_files>
</skill_content>"""

    return ToolResult(success=True, output=output.strip())
