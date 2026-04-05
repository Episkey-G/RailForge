import json
import subprocess
import sys
from pathlib import Path


def _run(workspace: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "railforge", *args, "--workspace", str(workspace)],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )


def test_spec_init_to_spec_review_hosted_smoke_flow(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    init = _run(workspace, "spec-init")
    assert init.returncode == 0
    assert json.loads(init.stdout)["status"] == "READY"

    research = _run(
        workspace,
        "spec-research",
        "--profile",
        "mock",
        "--scenario",
        "hosted-smoke",
        "--request",
        "后端接口必须拒绝过去日期。前端需要显示明确错误提示。需要补齐测试。",
    )
    assert research.returncode == 0
    assert research.stdout.strip().endswith("BLOCKED")

    approve_spec = _run(workspace, "approve", "--target", "spec")
    assert approve_spec.returncode == 0

    plan = _run(workspace, "spec-plan", "--profile", "mock", "--scenario", "hosted-smoke")
    assert plan.returncode == 0
    assert plan.stdout.strip().endswith("BLOCKED")

    approve_backlog = _run(workspace, "approve", "--target", "backlog")
    assert approve_backlog.returncode == 0
    approve_contract = _run(workspace, "approve", "--target", "contract")
    assert approve_contract.returncode == 0

    for _ in range(5):
        prepare = _run(workspace, "prepare-execution", "--profile", "mock", "--scenario", "hosted-smoke")
        assert prepare.returncode == 0
        request = json.loads(prepare.stdout)
        changed_path = request["allowed_paths"][0] + "smoke_artifact.txt"
        result_file = workspace / f'{request["task_id"]}.json'
        result_file.write_text(
            json.dumps(
                {
                    "task_id": request["task_id"],
                    "summary": f'hosted smoke finished {request["task_id"]}',
                    "changed_files": [changed_path],
                    "verification_notes": request["verification"],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        recorded = _run(
            workspace,
            "record-execution",
            "--profile",
            "mock",
            "--scenario",
            "hosted-smoke",
            "--file",
            str(result_file),
        )
        assert recorded.returncode == 0
        if recorded.stdout.strip().endswith("DONE"):
            break
        assert recorded.stdout.strip().endswith("BLOCKED")
    else:
        raise AssertionError("hosted smoke did not reach DONE within expected task iterations")

    review = _run(workspace, "spec-review", "--profile", "mock", "--scenario", "hosted-smoke")
    payload = json.loads(review.stdout)

    assert review.returncode == 0
    assert payload["scope"] == "change"
    assert payload["status"] == "approved"
    assert (workspace / "docs" / "quality" / "active" / "final_review.json").exists()
