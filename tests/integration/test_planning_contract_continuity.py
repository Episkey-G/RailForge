import subprocess
import sys
from pathlib import Path

import yaml


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "railforge", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_spec_plan_uses_ready_planning_contract_scope_for_site_delivery(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    research = _run(
        "spec-research",
        "--workspace",
        str(workspace),
        "--request",
        "为 PulseNotch 做双语静态介绍页，输出 landing page、共享 assets，并保持 clean-room。",
    )
    assert research.returncode == 0
    assert research.stdout.strip().endswith("BLOCKED")

    _run("approve", "--workspace", str(workspace), "--target", "spec")
    planning_dir = workspace / ".railforge" / "planning"
    planning_dir.mkdir(parents=True, exist_ok=True)
    contract_path = planning_dir / "contract.yaml"
    contract_path.write_text(
        yaml.safe_dump(
            {
                "change": "PulseNotch",
                "status": "ready_for_impl",
                "write_scope": {
                    "allowed_paths": [
                        str(workspace / "site" / "**"),
                        str(workspace / "openspec" / "changes" / "PulseNotch" / "**"),
                        str(workspace / ".railforge" / "planning" / "**"),
                    ]
                },
                "deliverables": [
                    "bilingual landing page under site/",
                    "shared asset layer under site/assets/",
                    "zero-decision OpenSpec artifacts for PulseNotch landing page",
                ],
                "locked_decisions": [
                    "provider 仅公开 Claude Code / Codex / Gemini CLI",
                    "页面遵守 clean-room 边界",
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = _run("spec-plan", "--workspace", str(workspace))

    backlog = yaml.safe_load((planning_dir / "backlog.draft.yaml").read_text(encoding="utf-8"))
    contract = yaml.safe_load((workspace / ".railforge" / "execution" / "tasks" / "T-001" / "contract.yaml").read_text(encoding="utf-8"))

    assert result.returncode == 0
    assert result.stdout.strip().endswith("BLOCKED")
    assert [item["title"] for item in backlog["items"]] == [
        "实现前端能力：bilingual landing page under site/",
        "实现前端能力：shared asset layer under site/assets/",
    ]
    assert backlog["items"][0]["allowed_paths"] == ["site/"]
    assert contract["allowed_paths"] == ["site/"]
    assert "provider 仅公开 Claude Code / Codex / Gemini CLI" in contract["done_definition"]
    assert any("规划交付物：bilingual landing page under site/" in item for item in contract["task_context"])
