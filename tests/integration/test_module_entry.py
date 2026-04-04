import subprocess
import sys
from pathlib import Path


def test_python_module_entry_runs_spec_research_and_blocks(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "railforge",
            "spec-research",
            "--workspace",
            str(tmp_path / "workspace"),
            "--request",
            "实现过去日期校验，时区规则和文案需要人工确认。",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip().endswith("BLOCKED")
