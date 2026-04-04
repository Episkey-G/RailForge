from pathlib import Path

import pytest

from railforge.core.models import ContractSpec, TaskItem, WorkspaceLayout
from railforge.orchestrator.contract_gate import ContractGate, ContractGateError
from railforge.orchestrator.interrupts import InterruptManager


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
    )


def test_contract_gate_rejects_missing_rollback() -> None:
    contract = _contract()
    contract.rollback = []

    with pytest.raises(ContractGateError):
        ContractGate().validate(task=_task(), contract=contract)


def test_interrupt_manager_roundtrip(tmp_path: Path) -> None:
    manager = InterruptManager(WorkspaceLayout(tmp_path))
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
