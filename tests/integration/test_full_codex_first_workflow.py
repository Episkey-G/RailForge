import subprocess
import sys
from pathlib import Path

import yaml


def test_full_codex_first_workflow_blocks_for_spec_then_executes(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    blocked = subprocess.run(
        [
            sys.executable,
            "-m",
            "railforge",
            "spec-research",
            "--workspace",
            str(workspace),
            "--request",
            "实现过去日期校验，时区规则和文案需要人工确认。",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert blocked.stdout.strip().endswith("BLOCKED")

    answers_path = workspace / "answers.yaml"
    answers_path.write_text(
        "answers:\n  Q-001: 业务口径已确认\n  Q-002: UTC\n  Q-003: 截止日期不能早于今天\n",
        encoding="utf-8",
    )
    assert subprocess.run(
        [sys.executable, "-m", "railforge", "answer", "--workspace", str(workspace), "--file", str(answers_path)],
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0

    spec_blocked = subprocess.run(
        [
            sys.executable,
            "-m",
            "railforge",
            "resume",
            "--workspace",
            str(workspace),
            "--reason",
            "clarification_resolved",
            "--note",
            "进入 spec 审批",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert spec_blocked.stdout.strip().endswith("BLOCKED")

    subprocess.run(
        [sys.executable, "-m", "railforge", "approve", "--workspace", str(workspace), "--target", "spec"],
        capture_output=True,
        text=True,
        check=False,
    )
    subprocess.run(
        [sys.executable, "-m", "railforge", "spec-plan", "--workspace", str(workspace)],
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

    executed = subprocess.run(
        [sys.executable, "-m", "railforge", "execute", "--workspace", str(workspace)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert executed.returncode == 0
    assert executed.stdout.strip().endswith("DONE")
    backlog = yaml.safe_load((workspace / ".railforge" / "planning" / "backlog.yaml").read_text(encoding="utf-8"))
    assert all(item["status"] == "done" for item in backlog["items"])
