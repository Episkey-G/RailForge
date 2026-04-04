import subprocess
from pathlib import Path


ROOT = Path("/Users/episkey/MyProjects/RailForge/RailForge")


def test_local_npx_menu_uses_arrow_prompt_in_tty() -> None:
    result = subprocess.run(
        ["script", "-q", "/dev/null", "npx", "railforge-workflow"],
        cwd=ROOT / "installer",
        capture_output=True,
        text=True,
        check=False,
    )

    output = result.stdout
    assert "↑↓ navigate" in output
    assert "选择操作编号或字母" not in output
