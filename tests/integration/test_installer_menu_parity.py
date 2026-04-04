from pathlib import Path


ROOT = Path("/Users/episkey/MyProjects/RailForge/RailForge")


def test_installer_menu_matches_ccg_style_sections() -> None:
    text = (ROOT / "installer" / "src" / "menu.mjs").read_text(encoding="utf-8")

    assert "RailForge Spec Workflow" in text
    assert "MCP 分组" in text
    assert "mainMenuChoices" in text
    assert "初始化 RailForge 配置" in text
    assert "配置模型路由" in text
    assert "卸载 RailForge" in text


def test_installer_command_templates_are_rich_like_ccg_spec_commands() -> None:
    text = (ROOT / "installer" / "src" / "commands.mjs").read_text(encoding="utf-8")

    assert "Core Philosophy" in text
    assert "Guardrails" in text
    assert "Hosted Codex" in text
    assert "Critical" in text
    assert "OpenSpec" in text
