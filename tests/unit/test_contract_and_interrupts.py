from pathlib import Path

import pytest

from railforge.artifacts.store import ArtifactStore
from railforge.core.enums import RunState
from railforge.core.models import ContractSpec, RunMeta, TaskItem, WorkspaceLayout
from railforge.orchestrator.contract_gate import ContractGate, ContractGateError
from railforge.orchestrator.interrupts import InterruptManager
from railforge.planner.contract_builder import build_contract


def _task() -> TaskItem:
    return TaskItem(
        id="T-001",
        title="Backend validation",
        status="ready",
        priority="high",
        depends_on=[],
        allowed_paths=["backend/", "tests/"],
        verification=["pytest tests/test_demo.py"],
        repair_budget=2,
        done_definition=["reject invalid input"],
    )


def _contract() -> ContractSpec:
    return ContractSpec(
        task_id="T-001",
        scope=["backend validation"],
        non_scope=["frontend"],
        allowed_paths=["backend/", "tests/"],
        verification=["pytest tests/test_demo.py"],
        rollback=["revert validator"],
        done_definition=["reject invalid input"],
        task_context=["当前任务聚焦后端校验"],
        writeback_requirements={
            "required_fields": ["task_id", "summary", "changed_files", "verification_notes"],
            "result_path": ".railforge/runtime/execution_results/run-1/T-001/hosted_codex.json",
        },
        role_boundaries={
            "lead_writer": {
                "read_only": False,
                "allowed_paths": ["backend/", "tests/", ".railforge/runtime/runs/run-1/tasks/T-001/"],
                "allowed_tools": ["shell", "git", "playwright"],
            },
            "backend_specialist": {
                "read_only": True,
                "allowed_paths": [
                    ".railforge/runtime/reviews/run-1/T-001/",
                    ".railforge/runtime/proposals/run-1/T-001/",
                ],
                "allowed_tools": ["shell", "search"],
            },
            "frontend_specialist": {
                "read_only": True,
                "allowed_paths": [
                    ".railforge/runtime/reviews/run-1/T-001/",
                    ".railforge/runtime/proposals/run-1/T-001/",
                ],
                "allowed_tools": ["shell", "playwright", "search"],
            },
            "backend_evaluator": {
                "read_only": True,
                "allowed_paths": [
                    ".railforge/runtime/reviews/run-1/T-001/",
                    ".railforge/runtime/proposals/run-1/T-001/",
                ],
                "allowed_tools": ["shell", "search"],
            },
            "frontend_evaluator": {
                "read_only": True,
                "allowed_paths": [
                    ".railforge/runtime/reviews/run-1/T-001/",
                    ".railforge/runtime/proposals/run-1/T-001/",
                ],
                "allowed_tools": ["shell", "playwright", "search"],
            },
        },
    )


def test_contract_gate_rejects_missing_rollback() -> None:
    contract = _contract()
    contract.rollback = []

    with pytest.raises(ContractGateError):
        ContractGate().validate(task=_task(), contract=contract)


def test_build_contract_includes_execution_context_and_boundaries() -> None:
    contract = build_contract(_task(), run_id="run-1")

    assert contract.task_context
    assert any("Backend validation" in item for item in contract.task_context)
    assert contract.writeback_requirements["required_fields"] == [
        "task_id",
        "summary",
        "changed_files",
        "verification_notes",
    ]
    assert contract.writeback_requirements["result_path"] == ".railforge/runtime/execution_results/run-1/T-001/hosted_codex.json"
    assert contract.role_boundaries["lead_writer"]["read_only"] is False
    assert contract.role_boundaries["backend_specialist"]["read_only"] is True
    assert contract.role_boundaries["frontend_specialist"]["read_only"] is True
    assert contract.role_boundaries["lead_writer"]["allowed_tools"] == ["shell", "git", "playwright"]
    assert contract.role_boundaries["backend_specialist"]["allowed_tools"] == ["shell", "search"]
    assert ".railforge/runtime/runs/run-1/tasks/T-001/" in contract.role_boundaries["lead_writer"]["allowed_paths"]
    assert ".railforge/runtime/reviews/run-1/T-001/" in contract.role_boundaries["backend_specialist"]["allowed_paths"]
    assert any("frontend/" in item for item in contract.non_scope)


def test_interrupt_manager_roundtrip(tmp_path: Path) -> None:
    layout = WorkspaceLayout(tmp_path)
    store = ArtifactStore(layout)
    store.init_workspace()
    store.save_run_state(
        RunMeta(
            run_id="run-1",
            state=RunState.BLOCKED,
            current_task_id="T-001",
            blocked_reason="manual_approval",
            resume_from_state="IMPLEMENTING",
        )
    )
    manager = InterruptManager(layout)
    payload = manager.record_blocked(
        task_id="T-001",
        reason="manual_approval",
        resume_from_state="IMPLEMENTING",
        note="need approval",
    )

    assert payload["reason"] == "manual_approval"

    manager.record_unblock(reason="approved", note="continue")
    decision = manager.load_unblock_decision()
    assert decision["reason"] == "approved"
