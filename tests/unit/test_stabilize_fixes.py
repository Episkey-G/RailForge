"""回归测试：stabilize-front-door-and-manual-repair-reentry 五项修复 + 评审修订"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from railforge.cli import _resolve_workspace
from railforge.core.enums import RunState
from railforge.core.models import ContractSpec, RunMeta, TaskItem
from railforge.guardrails.blocker_detector import detect_blocker
from railforge.orchestrator.contract_gate import ContractGate


# --- 修复 1: 前门 workspace 解析 ---


def test_resolve_workspace_finds_railforge_marker(tmp_path: Path) -> None:
    rf_dir = tmp_path / ".railforge"
    rf_dir.mkdir()
    sub = tmp_path / "deep" / "nested"
    sub.mkdir(parents=True)
    old_cwd = os.getcwd()
    try:
        os.chdir(str(sub))
        assert _resolve_workspace(None) == tmp_path
    finally:
        os.chdir(old_cwd)


def test_resolve_workspace_finds_git_marker(tmp_path: Path) -> None:
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    sub = tmp_path / "src"
    sub.mkdir()
    old_cwd = os.getcwd()
    try:
        os.chdir(str(sub))
        assert _resolve_workspace(None) == tmp_path
    finally:
        os.chdir(old_cwd)


def test_resolve_workspace_errors_when_no_marker(tmp_path: Path) -> None:
    old_cwd = os.getcwd()
    try:
        os.chdir(str(tmp_path))
        with pytest.raises(SystemExit, match="No RailForge workspace detected"):
            _resolve_workspace(None)
    finally:
        os.chdir(old_cwd)


def test_resolve_workspace_explicit_overrides(tmp_path: Path) -> None:
    explicit = tmp_path / "my_workspace"
    explicit.mkdir()
    assert _resolve_workspace(str(explicit)) == explicit


# --- 修复 4: repair 根因保留 + recovery_action ---


def test_blocker_detector_preserves_root_cause() -> None:
    run = RunMeta(
        run_id="run-1",
        state=RunState.REPAIRING,
        repair_count=3,
    )
    task = TaskItem(
        id="T-001",
        title="test",
        status="in_progress",
        priority="high",
        depends_on=[],
        allowed_paths=["backend/"],
        verification=["pytest"],
        repair_budget=2,
    )
    result = detect_blocker(run=run, task=task)
    assert result.blocked is True
    assert result.reason == "repair_budget_exhausted"
    assert result.resume_from_state == "STATIC_REVIEW"


def test_blocker_detector_repeated_failure_preserves_reason() -> None:
    run = RunMeta(run_id="run-1", state=RunState.REPAIRING, repair_count=0)
    task = TaskItem(
        id="T-001", title="test", status="in_progress", priority="high",
        depends_on=[], allowed_paths=["backend/"], verification=["pytest"], repair_budget=3,
    )
    result = detect_blocker(run=run, task=task, repeated_failure=True)
    assert result.blocked is True
    assert result.reason == "repeated_failure_signature"
    assert result.resume_from_state == "STATIC_REVIEW"


def test_run_meta_has_recovery_action_field() -> None:
    meta = RunMeta(run_id="r", state=RunState.BLOCKED, recovery_action="manual_repair")
    d = meta.to_dict()
    assert d["recovery_action"] == "manual_repair"
    restored = RunMeta.from_dict(d)
    assert restored.recovery_action == "manual_repair"


# --- 修复 5: repo reality audit 在 ContractGate ---


def test_contract_gate_repo_reality_passes_when_paths_exist(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / "backend").mkdir()
    (tmp_path / "tests").mkdir()
    gate = ContractGate()
    contract = ContractSpec(
        task_id="T-001", scope=["x"], non_scope=[], allowed_paths=["backend/", "tests/"],
        verification=["pytest"], rollback=["git checkout ."], done_definition=["done"],
        writeback_requirements={},
    )
    task = TaskItem(
        id="T-001", title="test", status="todo", priority="high",
        depends_on=[], allowed_paths=["backend/", "tests/"], verification=["pytest"], repair_budget=2,
    )
    assert gate.validate_repo_reality(tmp_path, contract, task) is None


def test_contract_gate_repo_reality_fails_when_paths_missing(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    gate = ContractGate()
    contract = ContractSpec(
        task_id="T-001", scope=["x"], non_scope=[], allowed_paths=["site/", "tests/"],
        verification=["pytest"], rollback=["git checkout ."], done_definition=["done"],
        writeback_requirements={},
    )
    task = TaskItem(
        id="T-001", title="test", status="todo", priority="high",
        depends_on=[], allowed_paths=["site/", "tests/"], verification=["pytest"], repair_budget=2,
    )
    result = gate.validate_repo_reality(tmp_path, contract, task)
    assert result is not None
    assert "site/" in result
    assert "tests/" in result


def test_contract_gate_repo_reality_allows_creates_root(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    gate = ContractGate()
    contract = ContractSpec(
        task_id="T-001", scope=["x"], non_scope=[], allowed_paths=["site/"],
        verification=["pytest"], rollback=["git checkout ."], done_definition=["done"],
        writeback_requirements={"creates_root": ["site/"]},
    )
    task = TaskItem(
        id="T-001", title="test", status="todo", priority="high",
        depends_on=[], allowed_paths=["site/"], verification=["pytest"], repair_budget=2,
    )
    assert gate.validate_repo_reality(tmp_path, contract, task) is None


def test_contract_gate_repo_reality_skips_non_git(tmp_path: Path) -> None:
    gate = ContractGate()
    contract = ContractSpec(
        task_id="T-001", scope=["x"], non_scope=[], allowed_paths=["nonexistent/"],
        verification=["pytest"], rollback=["git checkout ."], done_definition=["done"],
        writeback_requirements={},
    )
    task = TaskItem(
        id="T-001", title="test", status="todo", priority="high",
        depends_on=[], allowed_paths=["nonexistent/"], verification=["pytest"], repair_budget=2,
    )
    assert gate.validate_repo_reality(tmp_path, contract, task) is None


# --- 修复 2: approve-and-resume blocked_reason 匹配 ---


def test_approval_gate_map_covers_all_targets() -> None:
    from railforge.application.workflow_commands import WorkflowCommandService
    assert "spec" in WorkflowCommandService._APPROVAL_GATE_MAP
    assert "backlog" in WorkflowCommandService._APPROVAL_GATE_MAP
    assert "contract" in WorkflowCommandService._APPROVAL_GATE_MAP


# --- doctor 分级 ---


def test_doctor_ready_after_init(tmp_path: Path) -> None:
    from railforge.application.workflow_commands import WorkflowCommandService
    svc = WorkflowCommandService(tmp_path)
    svc.store.init_workspace()
    # 创建最小依赖
    svc.layout.models_path.parent.mkdir(parents=True, exist_ok=True)
    svc.layout.models_path.write_text("lead_writer: mock\n")
    svc.layout.skills_dir.mkdir(parents=True, exist_ok=True)
    result = svc._diagnose_readiness()
    # 没有 critical 问题即可 READY 或 DEGRADED
    assert result["status"] in {"READY", "DEGRADED"}


def test_doctor_blocked_without_runtime(tmp_path: Path) -> None:
    from railforge.application.workflow_commands import WorkflowCommandService
    svc = WorkflowCommandService(tmp_path)
    # 不初始化任何目录
    result = svc._diagnose_readiness()
    assert result["status"] == "BLOCKED"
    assert any("CRITICAL" in i for i in result["issues"])
