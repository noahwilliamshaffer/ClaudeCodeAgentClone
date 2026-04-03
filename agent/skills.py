"""Load skill markdown files from /skills."""

from __future__ import annotations

from pathlib import Path


def load_skill(skills_dir: Path, skill_id: str) -> str:
    path = skills_dir / f"{skill_id}.md"
    if not path.is_file():
        return f"(skill not found: {skill_id})"
    return path.read_text(encoding="utf-8")


def list_skills(skills_dir: Path) -> list[str]:
    if not skills_dir.is_dir():
        return []
    return sorted(p.stem for p in skills_dir.glob("*.md") if p.name.lower() != "readme.md")
