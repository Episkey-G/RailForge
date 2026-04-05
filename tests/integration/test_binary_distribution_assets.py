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


def test_build_workflow_publishes_release_assets() -> None:
    text = (ROOT / ".github" / "workflows" / "build-binaries.yml").read_text(encoding="utf-8")
    assert "softprops/action-gh-release" in text
    commands = (ROOT / "installer" / "src" / "commands.mjs").read_text(encoding="utf-8")
    assert "releases/download/" in commands
    assert "railforge-v${RAILFORGE_BINARY_VERSION}" in commands
    build_script = (ROOT / "scripts" / "build_binaries.py").read_text(encoding="utf-8")
    assert "manifest-" in build_script
    assert "sha256" in build_script


def test_readme_documents_generic_binary_install_paths() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "~/.codex/bin/railforge" in text
    assert "~/.codex/bin/railforge-codeagent" in text
