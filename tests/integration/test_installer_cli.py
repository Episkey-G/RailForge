import json
import subprocess
from pathlib import Path


ROOT = Path("/Users/episkey/MyProjects/RailForge/RailForge")
INSTALLER = ROOT / "installer" / "bin" / "railforge.mjs"


def test_installer_init_scaffolds_project_files(tmp_path: Path) -> None:
    target = tmp_path / "demo"

    result = subprocess.run(
        ["node", str(INSTALLER), "init", "--target", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "init"
    assert payload["status"] == "installed"
    assert (target / ".agents" / "skills" / "rf-spec-init" / "SKILL.md").exists()
    assert (target / ".claude" / "commands" / "rf" / "spec-init.md").exists()
    assert (target / ".railforge" / "runtime" / "models.yaml").exists()
    assert (target / "openspec" / "changes").exists()
    assert (target / ".mcp.json").exists()
    assert (target / "AGENTS.md").exists()


def test_installer_uninstall_removes_scaffolded_files(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    subprocess.run(
        ["node", str(INSTALLER), "init", "--target", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )

    result = subprocess.run(
        ["node", str(INSTALLER), "uninstall", "--target", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "uninstall"
    assert payload["status"] == "removed"
    assert not (target / ".agents").exists()
    assert not (target / ".claude" / "commands" / "rf").exists()


def test_installer_config_mcp_writes_catalog(tmp_path: Path) -> None:
    target = tmp_path / "demo"

    result = subprocess.run(
        ["node", str(INSTALLER), "config-mcp", "--target", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "config-mcp"
    assert (target / ".mcp.json").exists()


def test_installer_help_lists_core_commands() -> None:
    result = subprocess.run(
        ["node", str(INSTALLER), "help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "menu" in result.stdout
    assert "init" in result.stdout
    assert "config-mcp" in result.stdout
    assert "doctor" in result.stdout
    assert "uninstall" in result.stdout


def test_installer_update_refreshes_project(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    subprocess.run(
        ["node", str(INSTALLER), "init", "--target", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )

    result = subprocess.run(
        ["node", str(INSTALLER), "update", "--target", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "update"
    assert payload["status"] == "updated"
    assert (target / ".agents" / "skills" / "rf-spec-impl" / "SKILL.md").exists()


def test_installer_config_model_writes_models_yaml(tmp_path: Path) -> None:
    target = tmp_path / "demo"

    result = subprocess.run(
        [
            "node",
            str(INSTALLER),
            "config-model",
            "--target",
            str(target),
            "--lead-writer",
            "codex_cli",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "config-model"
    models = (target / ".railforge" / "runtime" / "models.yaml").read_text(encoding="utf-8")
    assert "driver: codex_cli" in models


def test_installer_probe_mcp_reports_configured_and_synced_files(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    subprocess.run(
        ["node", str(INSTALLER), "config-mcp", "--target", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )

    result = subprocess.run(
        ["node", str(INSTALLER), "probe-mcp", "--target", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "probe-mcp"
    assert "context7" in payload["configured"]
    assert str(target / ".codex" / "config.toml") in payload["mirrors"]
    assert str(target / ".gemini" / "settings.json") in payload["mirrors"]
