from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_skill_frontmatter_names_match_directories():
    skill_files = sorted((ROOT / "skills").glob("*/SKILL.md"))
    assert skill_files

    for skill_file in skill_files:
        text = skill_file.read_text()
        _, frontmatter, _ = text.split("---", 2)
        metadata = yaml.safe_load(frontmatter)
        assert metadata["name"] == skill_file.parent.name
        assert metadata["description"]
        assert metadata["when_to_use"]
