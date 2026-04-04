import subprocess
import sys
from pathlib import Path


def test_spec_research_writes_openspec_proposal(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "railforge",
            "spec-research",
            "--workspace",
            str(workspace),
            "--project",
            "user-auth",
            "--request",
            "Implement user authentication",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    proposal = workspace / "openspec" / "changes" / "user-auth" / "proposal.md"
    assert proposal.exists()


def test_spec_plan_writes_openspec_design_and_tasks(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "railforge",
            "spec-research",
            "--workspace",
            str(workspace),
            "--project",
            "user-auth",
            "--request",
            "Implement user authentication",
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

    result = subprocess.run(
        [sys.executable, "-m", "railforge", "spec-plan", "--workspace", str(workspace)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    change_dir = workspace / "openspec" / "changes" / "user-auth"
    assert (change_dir / "design.md").exists()
    assert (change_dir / "tasks.md").exists()
    assert (change_dir / "specs" / "harness-core" / "spec.md").exists()
