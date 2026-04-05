import json
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


def _active_run_id(workspace: Path) -> str:
    return json.loads((workspace / ".railforge" / "runtime" / "current_run.json").read_text(encoding="utf-8"))["run_id"]


def test_spec_research_writes_structured_proposal_from_clarification(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    result = _run(
        "spec-research",
        "--workspace",
        str(workspace),
        "--request",
        "实现过去日期校验，时区规则和文案需要人工确认。",
    )

    proposal = (workspace / "openspec" / "changes" / "workspace" / "proposal.md").read_text(encoding="utf-8")

    assert result.returncode == 0
    assert result.stdout.strip().endswith("BLOCKED")
    assert "# Proposal" in proposal
    assert "## 原始需求" in proposal
    assert "## 需求摘要" in proposal
    assert "## 约束" in proposal
    assert "## HITL 问题" in proposal
    assert "Q-001" in proposal
    assert "Q-002" in proposal
    assert "## 决策点" in proposal
    assert "D-001" in proposal
    assert "## 下一步" in proposal


def test_spec_plan_generates_requirement_driven_backlog_and_contracts(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    _run(
        "spec-research",
        "--workspace",
        str(workspace),
        "--request",
        "后端校验、前端提示、测试覆盖。",
    )
    _run("approve", "--workspace", str(workspace), "--target", "spec")

    result = _run("spec-plan", "--workspace", str(workspace))

    design = (workspace / "openspec" / "changes" / "workspace" / "design.md").read_text(encoding="utf-8")
    tasks = (workspace / "openspec" / "changes" / "workspace" / "tasks.md").read_text(encoding="utf-8")
    spec = (
        workspace / "openspec" / "changes" / "workspace" / "specs" / "harness-core" / "spec.md"
    ).read_text(encoding="utf-8")
    contract = (
        workspace / ".railforge" / "runtime" / "runs" / _active_run_id(workspace) / "tasks" / "T-001" / "contract.yaml"
    ).read_text(encoding="utf-8")
    backlog = yaml.safe_load((workspace / "docs" / "exec-plans" / "active" / "backlog.draft.yaml").read_text(encoding="utf-8"))

    assert result.returncode == 0
    assert result.stdout.strip().endswith("BLOCKED")
    assert "## Summary" in design
    assert "## Constraints" in design
    assert "## Decision Points" in design
    assert "- [ ] T-001 实现后端能力：后端校验" in tasks
    assert "Allowed Paths: backend/, tests/" in tasks
    assert "Verification: pytest tests/test_backend_flow.py" in tasks
    assert "# Spec" in spec
    assert "## Requirements" in spec
    assert "## Approval Gates" in spec
    assert [item["title"] for item in backlog["items"]] == [
        "实现后端能力：后端校验",
        "实现前端能力：前端提示",
        "补齐验证：测试覆盖",
    ]
    assert "allowed_paths:" in contract
    assert "backend/" in contract
    assert "pytest tests/test_backend_flow.py" in contract


def test_spec_plan_refuses_to_progress_with_unresolved_questions(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    _run(
        "spec-research",
        "--workspace",
        str(workspace),
        "--request",
        "实现过去日期校验，时区规则和文案需要人工确认。",
    )
    _run("approve", "--workspace", str(workspace), "--target", "spec")

    result = _run("spec-plan", "--workspace", str(workspace))

    assert result.returncode == 0
    assert result.stdout.strip().endswith("BLOCKED")
    assert not (workspace / "docs" / "exec-plans" / "active" / "backlog.draft.yaml").exists()


def test_spec_review_runs_independent_dual_model_gate_and_writes_review_artifacts(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    _run(
        "spec-research",
        "--workspace",
        str(workspace),
        "--request",
        "后端校验、前端提示、测试覆盖。",
        "--scenario",
        "repeated-failure",
    )
    _run("approve", "--workspace", str(workspace), "--target", "spec")
    _run("spec-plan", "--workspace", str(workspace), "--scenario", "repeated-failure")
    _run("approve", "--workspace", str(workspace), "--target", "backlog")
    _run("approve", "--workspace", str(workspace), "--target", "contract")
    execute = _run("execute", "--workspace", str(workspace), "--scenario", "repeated-failure")

    review = _run("review", "--workspace", str(workspace), "--scenario", "repeated-failure")
    spec_review = _run("spec-review", "--workspace", str(workspace), "--scenario", "repeated-failure")
    run_id = _active_run_id(workspace)
    task_dir = workspace / ".railforge" / "runtime" / "runs" / run_id / "tasks" / "T-001"
    review_dir = workspace / ".railforge" / "runtime" / "reviews" / run_id / "T-001"
    trace_dir = workspace / ".railforge" / "runtime" / "traces" / run_id / "T-001"
    payload = json.loads(spec_review.stdout)

    assert execute.returncode == 0
    assert execute.stdout.strip().endswith("BLOCKED")
    assert review.returncode == 0
    assert spec_review.returncode == 0
    assert json.loads(spec_review.stdout)["status"] == "failed"
    assert payload["mode"] == "spec_review"
    assert payload["scope"] == "task"
    assert payload["task_id"] == "T-001"
    assert payload["aggregate"]["status"] == "failed"
    assert payload["aggregate"]["severity_counts"]["critical"] >= 1
    assert payload["qa_report"]["review"]["mode"] == "spec_review"
    assert payload["qa_report"]["backend"]["status"] == "passed"
    assert payload["qa_report"]["frontend"]["status"] == "passed"
    assert payload["qa_report"] != json.loads(review.stdout)
    assert (task_dir / "qa_report.json").exists()
    assert (review_dir / "spec_review.json").exists()
    assert (review_dir / "backend_evaluator.md").exists()
    assert (review_dir / "frontend_evaluator.md").exists()
    assert (trace_dir / "backend_evaluator.json").exists()
    assert (trace_dir / "frontend_evaluator.json").exists()
