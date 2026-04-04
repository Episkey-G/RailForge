import subprocess
import sys
from pathlib import Path


def test_spec_init_bootstraps_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    result = subprocess.run(
        [sys.executable, "-m", "railforge", "spec-init", "--workspace", str(workspace)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0


def test_spec_impl_acts_as_primary_execution_entry(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    result = subprocess.run(
        [sys.executable, "-m", "railforge", "spec-impl", "--workspace", str(workspace)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0


def test_spec_review_is_available_as_top_level_command(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    result = subprocess.run(
        [sys.executable, "-m", "railforge", "spec-review", "--workspace", str(workspace)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
