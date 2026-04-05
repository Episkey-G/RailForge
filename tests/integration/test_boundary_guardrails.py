import subprocess
import sys
from pathlib import Path


ROOT = Path("/Users/episkey/MyProjects/RailForge/RailForge")


def test_boundary_guardrail_script_and_hook_exist() -> None:
    script = ROOT / "scripts" / "check_boundaries.py"
    hook = ROOT / ".githooks" / "pre-commit"

    assert script.exists()
    assert hook.exists()
    assert "check_boundaries.py" in hook.read_text(encoding="utf-8")


def test_boundary_guardrail_script_passes_for_repo() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_boundaries.py"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_commands_facade_stays_small() -> None:
    line_count = len((ROOT / "railforge" / "commands.py").read_text(encoding="utf-8").splitlines())

    assert line_count <= 100
