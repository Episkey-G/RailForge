import subprocess
import sys
from pathlib import Path


def test_execute_reaches_repair_and_resume_finishes(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "railforge",
            "spec-research",
            "--workspace",
            str(workspace),
            "--request",
            "后端校验、前端提示、测试覆盖。",
            "--scenario",
            "repeated-failure",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    subprocess.run(
        [sys.executable, "-m", "railforge", "approve", "--workspace", str(workspace), "--target", "spec"],
        capture_output=True,
        text=True,
        check=False,
    )
    subprocess.run(
        [sys.executable, "-m", "railforge", "spec-plan", "--workspace", str(workspace), "--scenario", "repeated-failure"],
        capture_output=True,
        text=True,
        check=False,
    )
    subprocess.run(
        [sys.executable, "-m", "railforge", "approve", "--workspace", str(workspace), "--target", "backlog"],
        capture_output=True,
        text=True,
        check=False,
    )
    subprocess.run(
        [sys.executable, "-m", "railforge", "approve", "--workspace", str(workspace), "--target", "contract"],
        capture_output=True,
        text=True,
        check=False,
    )

    blocked = subprocess.run(
        [sys.executable, "-m", "railforge", "execute", "--workspace", str(workspace), "--scenario", "repeated-failure"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert blocked.returncode == 0
    assert blocked.stdout.strip().endswith("BLOCKED")

    review = subprocess.run(
        [sys.executable, "-m", "railforge", "review", "--workspace", str(workspace), "--scenario", "repeated-failure"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert review.returncode == 0

    resumed = subprocess.run(
        [
            sys.executable,
            "-m",
            "railforge",
            "resume",
            "--workspace",
            str(workspace),
            "--reason",
            "manual_override",
            "--note",
            "继续修复",
            "--scenario",
            "repeated-failure",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert resumed.returncode == 0
    assert resumed.stdout.strip().endswith("DONE")
