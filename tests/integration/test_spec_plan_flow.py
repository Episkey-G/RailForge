import subprocess
import sys
from pathlib import Path

import yaml


def test_spec_plan_generates_backlog_draft_after_spec_approval(tmp_path: Path) -> None:
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
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "railforge",
            "approve",
            "--workspace",
            str(workspace),
            "--target",
            "spec",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "railforge",
            "spec-plan",
            "--workspace",
            str(workspace),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip().endswith("BLOCKED")
    backlog = yaml.safe_load((workspace / "docs" / "exec-plans" / "active" / "backlog.draft.yaml").read_text(encoding="utf-8"))
    assert len(backlog["items"]) == 3
