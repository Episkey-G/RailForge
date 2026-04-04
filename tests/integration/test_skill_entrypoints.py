from __future__ import annotations

import stat
from pathlib import Path


EXPECTED_SKILLS = {
    "rf-spec-init": "spec-init",
    "rf-spec-research": "spec-research",
    "rf-spec-plan": "spec-plan",
    "rf-spec-impl": "spec-impl",
    "rf-spec-review": "spec-review",
    "rf-execute": "execute",
    "rf-review": "review",
    "rf-resume": "resume",
    "rf-status": "status",
}


def test_skill_entrypoints_exist_and_call_expected_commands() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    readme = (repo_root / "README.md").read_text()

    assert "Codex CLI" in readme
    assert "spec-research" in readme
    assert "spec-plan" in readme
    assert "HITL" in readme
    assert "hosted_codex" in readme
    assert "prepare-execution" in readme
    assert "record-execution" in readme
    assert "docs/architecture/" in readme
    assert "docs/railforge/architecture/" not in readme
    assert (repo_root / "docs" / "architecture").exists()
    assert not (repo_root / "docs" / "superpowers").exists()

    for skill_name, command in EXPECTED_SKILLS.items():
        skill_dir = repo_root / ".agents" / "skills" / skill_name
        skill_file = skill_dir / "SKILL.md"
        script_file = skill_dir / "scripts" / "run.sh"

        assert skill_file.exists()
        assert script_file.exists()
        assert skill_file.read_text().startswith("---\nname: ")
        assert f"name: {skill_name}" in skill_file.read_text()
        assert f"python -m railforge {command}" in script_file.read_text()
        assert script_file.stat().st_mode & stat.S_IXUSR
