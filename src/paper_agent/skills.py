"""Validate and load the same skill files that are distributed to host agents."""

import re
from pathlib import Path

import yaml

from .storage import ValidationError, digest

DEFAULT_SKILLS = Path(__file__).parent / "skills"


def load_skills(directory=None, names=None):
    directory = Path(directory) if directory else DEFAULT_SKILLS
    skills = []
    for path in sorted(directory.glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
        if not match:
            raise ValidationError(f"Missing YAML frontmatter: {path}")
        try:
            metadata = yaml.safe_load(match[1])
        except yaml.YAMLError as exc:
            raise ValidationError(f"Invalid skill YAML: {path}") from exc
        if not isinstance(metadata, dict):
            raise ValidationError(f"Skill metadata must be a mapping: {path}")
        name = metadata.get("name")
        description = metadata.get("description")
        if (not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)
                or len(name) > 64 or name != path.parent.name):
            raise ValidationError(f"Skill name must match its directory: {path}")
        if not isinstance(description, str) or not 1 <= len(description.strip()) <= 1024:
            raise ValidationError(f"Skill needs a concise description: {path}")
        references = {}
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            local = (path.parent / target.split("#")[0]).resolve()
            if not local.is_relative_to(path.parent.resolve()) or not local.is_file():
                raise ValidationError(f"Missing or nonlocal skill reference: {path}: {target}")
            references[target] = local.read_text(encoding="utf-8")
        if names is None or name in names:
            skills.append({"name": name, "description": description,
                           "text": text, "sha256": digest(text), "references": references})
    if names and set(names) != {s["name"] for s in skills}:
        raise ValidationError(f"Requested skills not found in {directory}: {names}")
    if not skills:
        raise ValidationError(f"No skills found in {directory}")
    return skills
