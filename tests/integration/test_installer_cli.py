from __future__ import annotations

import json
import os
import platform
import site
import subprocess
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

import pytest


ROOT = Path("/Users/episkey/MyProjects/RailForge/RailForge")
INSTALLER = ROOT / "installer" / "bin" / "railforge.mjs"
DEFAULT_INSTALLER_ENV = {**os.environ, "RAILFORGE_SKIP_BINARY_INSTALL": "1"}


def run_installer(*args: str, cwd: Optional[Path] = None, env: Optional[dict[str, str]] = None) -> subprocess.CompletedProcess[str]:
    merged_env = dict(DEFAULT_INSTALLER_ENV)
    if env:
        merged_env.update(env)
    return subprocess.run(
        ["node", str(INSTALLER), *args],
        cwd=cwd,
        env=merged_env,
        capture_output=True,
        text=True,
        check=False,
    )


def binary_suffix() -> str:
    arch = "arm64" if platform.machine().lower() in {"arm64", "aarch64"} else "amd64"
    if sys.platform == "darwin":
        system = "darwin"
    elif sys.platform == "win32":
        system = "windows"
    else:
        system = "linux"
    return f"{system}-{arch}"


def binary_asset_names() -> tuple[str, str]:
    ext = ".exe" if sys.platform == "win32" else ""
    suffix = binary_suffix()
    return (f"railforge-{suffix}{ext}", f"railforge-codeagent-{suffix}{ext}")


def test_installer_init_scaffolds_project_files(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    codex_root = target / ".codex"

    result = run_installer("init", "--target", str(target))

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "init"
    assert payload["status"] == "installed"
    assert payload["target"] == str(codex_root)
    assert (codex_root / "bin").exists()
    assert (codex_root / "skills" / "railforge" / "rf-spec-init" / "SKILL.md").exists()
    assert (codex_root / ".railforge" / "models.yaml").exists()
    assert (codex_root / ".railforge" / "policies.yaml").exists()
    assert (codex_root / ".railforge" / "binaries.json").exists()
    assert (codex_root / ".railforge" / "installer-state.json").exists()
    assert (codex_root / "AGENTS.md").exists()
    assert not (target / "AGENTS.md").exists()
    assert not (target / ".agents").exists()
    assert not (target / ".claude" / "commands" / "rf").exists()
    assert not (target / "openspec").exists()


def test_installer_init_scaffolds_openspec_bridge_entries(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    codex_root = target / ".codex"

    result = run_installer("init", "--target", str(target))

    assert result.returncode == 0
    assert (codex_root / "skills" / "railforge" / "rf-openspec-apply" / "SKILL.md").exists()
    assert (codex_root / "skills" / "railforge" / "rf-openspec-archive" / "SKILL.md").exists()
    assert not (target / ".claude" / "commands" / "rf" / "openspec-apply.md").exists()
    assert not (target / ".claude" / "commands" / "rf" / "openspec-archive.md").exists()


def test_installer_uninstall_removes_scaffolded_files(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    codex_root = target / ".codex"
    run_installer("init", "--target", str(target))

    result = run_installer("uninstall", "--target", str(target))

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "uninstall"
    assert payload["status"] == "removed"
    assert not (codex_root / "skills" / "railforge").exists()
    assert not (codex_root / ".railforge").exists()


def test_installer_uninstall_preserves_user_codex_and_mcp_content(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    codex_root = target / ".codex"
    claude_mcp = target / ".claude" / ".mcp.json"
    gemini_settings = target / ".gemini" / "settings.json"
    codex_config = codex_root / "config.toml"
    codex_agents = codex_root / "AGENTS.md"

    codex_root.mkdir(parents=True, exist_ok=True)
    claude_mcp.parent.mkdir(parents=True, exist_ok=True)
    gemini_settings.parent.mkdir(parents=True, exist_ok=True)
    codex_config.write_text('model = "gpt-5.4"\ncustom_key = "keep"\n', encoding="utf-8")
    codex_agents.write_text("# User AGENTS\nkeep me\n", encoding="utf-8")
    claude_mcp.write_text('{"mcpServers":{"userTool":{"command":"user"}}}', encoding="utf-8")
    gemini_settings.write_text('{"mcpServers":{"userTool":{"command":"user"}}}', encoding="utf-8")

    run_installer("init", "--target", str(target))
    result = run_installer("uninstall", "--target", str(target))

    assert result.returncode == 0
    assert codex_root.exists()
    assert 'custom_key = "keep"' in codex_config.read_text(encoding="utf-8")
    assert "railforge" not in codex_agents.read_text(encoding="utf-8").lower()
    assert "keep me" in codex_agents.read_text(encoding="utf-8")
    assert "userTool" in claude_mcp.read_text(encoding="utf-8")
    assert "userTool" in gemini_settings.read_text(encoding="utf-8")


def test_installer_config_mcp_writes_catalog(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    codex_root = target / ".codex"

    result = run_installer("config-mcp", "--target", str(target))

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "config-mcp"
    assert (codex_root / ".railforge" / "mcp.json").exists()
    codex_config = (codex_root / "config.toml").read_text(encoding="utf-8")
    assert 'model_reasoning_effort = "high"' in codex_config
    assert 'sandbox_mode = "workspace-write"' in codex_config
    assert "[mcp_servers.Context7]" in codex_config
    assert "startup_timeout_sec = 30" in codex_config


def test_installer_help_lists_core_commands() -> None:
    result = run_installer("help")

    assert result.returncode == 0
    assert "menu" in result.stdout
    assert "init" in result.stdout
    assert "config-mcp" in result.stdout
    assert "doctor" in result.stdout
    assert "uninstall" in result.stdout


def test_installer_update_refreshes_project(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    codex_root = target / ".codex"
    run_installer("init", "--target", str(target))

    result = run_installer("update", "--target", str(target))

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "update"
    assert payload["status"] == "updated"
    assert (codex_root / "skills" / "railforge" / "rf-spec-impl" / "SKILL.md").exists()


def test_installer_config_model_writes_models_yaml(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    codex_root = target / ".codex"

    result = run_installer(
        "config-model",
        "--target",
        str(target),
        "--lead-writer",
        "codex_cli",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "config-model"
    models = (codex_root / ".railforge" / "models.yaml").read_text(encoding="utf-8")
    assert "driver: codex_cli" in models


def test_installer_init_defaults_to_home_codex_namespace(tmp_path: Path) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir(parents=True, exist_ok=True)

    result = run_installer("init", cwd=tmp_path, env={"HOME": str(fake_home)})

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["target"] == str(fake_home / ".codex")
    assert (fake_home / ".codex" / "skills" / "railforge" / "rf-spec-init" / "SKILL.md").exists()


def test_installer_probe_mcp_reports_configured_and_synced_files(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    codex_root = target / ".codex"
    run_installer("config-mcp", "--target", str(target))

    result = run_installer("probe-mcp", "--target", str(target))

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "probe-mcp"
    assert "Context7" in payload["configured"]
    assert str(codex_root / "config.toml") in payload["mirrors"]
    assert str(target / ".gemini" / "settings.json") in payload["mirrors"]


def test_installer_user_level_to_project_init_and_uninstall_smoke(tmp_path: Path) -> None:
    home_root = tmp_path / "home"
    project_root = tmp_path / "project"
    home_root.mkdir(parents=True, exist_ok=True)
    project_root.mkdir(parents=True, exist_ok=True)

    env = {
        **DEFAULT_INSTALLER_ENV,
        "HOME": str(home_root),
        "PYTHONPATH": os.pathsep.join([str(ROOT), site.getusersitepackages()]),
        "RAILFORGE_PYTHON_BIN": sys.executable,
    }

    init_result = run_installer("init", "--target", str(home_root), env=env)
    assert init_result.returncode == 0

    codex_root = home_root / ".codex"
    init_script = codex_root / "skills" / "railforge" / "rf-spec-init" / "scripts" / "run.sh"
    assert init_script.exists()
    assert (home_root / ".claude" / ".mcp.json").exists()
    assert (home_root / ".gemini" / "settings.json").exists()

    skill_result = subprocess.run(
        [str(init_script)],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert skill_result.returncode == 0
    assert project_root.joinpath("openspec", "changes").exists()
    assert project_root.joinpath(".railforge", "runtime", "models.yaml").exists()

    uninstall_result = run_installer("uninstall", "--target", str(home_root), env=env)
    assert uninstall_result.returncode == 0
    assert not codex_root.joinpath("skills", "railforge").exists()
    assert not codex_root.joinpath(".railforge").exists()
    assert project_root.joinpath("openspec", "changes").exists()
    assert project_root.joinpath(".railforge", "runtime", "models.yaml").exists()


@pytest.mark.skipif(sys.platform == "win32", reason="测试使用 Unix shell 伪二进制")
def test_installer_downloads_release_binaries_into_codex_bin(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    release_root = tmp_path / "release"
    release_root.mkdir(parents=True, exist_ok=True)
    railforge_asset, codeagent_asset = binary_asset_names()

    binary_template = """#!/bin/sh
if [ "${1:-}" = "--version" ]; then
  echo "0.1.7"
  exit 0
fi
echo "ok"
"""
    for asset_name in (railforge_asset, codeagent_asset):
        asset_path = release_root / asset_name
        asset_path.write_text(binary_template, encoding="utf-8")
        asset_path.chmod(0o755)

    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(release_root)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = run_installer(
            "init",
            "--target",
            str(target),
            env={
                "RAILFORGE_SKIP_BINARY_INSTALL": "0",
                "RAILFORGE_BINARY_BASE_URL": f"http://127.0.0.1:{server.server_port}",
            },
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    railforge_bin = target / ".codex" / "bin" / "railforge"
    codeagent_bin = target / ".codex" / "bin" / "railforge-codeagent"
    assert railforge_bin.exists()
    assert codeagent_bin.exists()
    assert payload["warnings"] == []
    assert {item["name"] for item in payload["binaries"]} == {"railforge", "railforge-codeagent"}
    assert subprocess.run([str(railforge_bin), "--version"], capture_output=True, text=True, check=False).stdout.strip() == "0.1.7"
