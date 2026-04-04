from pathlib import Path


ROOT = Path("/Users/episkey/MyProjects/RailForge/RailForge")


def test_binary_build_script_and_workflow_exist() -> None:
    assert (ROOT / "scripts" / "build_binaries.py").exists()
    assert (ROOT / ".github" / "workflows" / "build-binaries.yml").exists()


def test_pyproject_declares_binary_build_dependency() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "pyinstaller" in text.lower()


def test_release_notes_cover_binary_distribution() -> None:
    text = (ROOT / "docs" / "guide" / "release-notes.md").read_text(encoding="utf-8")
    assert "二进制" in text
    assert "~/.codex/bin/" in text
