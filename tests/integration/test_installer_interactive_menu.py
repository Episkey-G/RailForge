import subprocess
from pathlib import Path


ROOT = Path("/Users/episkey/MyProjects/RailForge/RailForge")


def test_local_npx_menu_uses_arrow_prompt_in_tty() -> None:
    result = subprocess.run(
        ["script", "-q", "/dev/null", "node", str(ROOT / "installer" / "bin" / "railforge.mjs")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    output = result.stdout
    assert "↑↓ navigate" in output
    assert "选择操作编号或字母" not in output
    assert "? ? RailForge 主菜单" not in output
    assert "Multi-Model Collaboration" in output
    assert "查看全部斜杠命令" in output
    assert output.count("初始化 RailForge 配置") == 1
