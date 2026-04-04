import json
import subprocess
import sys
from pathlib import Path


def test_codeagent_cli_probe_prints_json(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "railforge.codeagent",
            "probe",
            "--backend",
            "claude",
            "--workspace",
            str(tmp_path),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["backend"] == "claude"


def test_codeagent_cli_run_accepts_inline_prompt(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "railforge.codeagent",
            "run",
            "--backend",
            "codex",
            "--role",
            "lead_writer",
            "--workspace",
            str(tmp_path),
            "--prompt",
            "hello",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["role"] == "lead_writer"
