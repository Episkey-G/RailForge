import subprocess
import sys
from pathlib import Path

import yaml


def test_spec_research_generates_draft_and_questions(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    result = subprocess.run(
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

    assert result.returncode == 0
    assert result.stdout.strip().endswith("BLOCKED")
    draft = yaml.safe_load((workspace / "docs" / "product-specs" / "active" / "product_spec.draft.yaml").read_text(encoding="utf-8"))
    questions = yaml.safe_load((workspace / "docs" / "product-specs" / "active" / "questions.yaml").read_text(encoding="utf-8"))
    assert draft["status"] == "draft"
    assert questions["unresolved"]
