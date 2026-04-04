from pathlib import Path

import pytest

from railforge.adapters.base import AdapterResult
from railforge.core.models import ContractSpec, RunMeta, TaskItem, WorkspaceLayout
from railforge.core.enums import RunState
from railforge.execution.backend_specialist import BackendSpecialistService
from railforge.execution.codex_writer import CodexWriterService
from railforge.execution.frontend_specialist import FrontendSpecialistService
from railforge.infra.file_lock import WorkspaceLock, WorkspaceLockError


class StubModelAdapter:
    def __init__(self) -> None:
        self.calls = []

    def invoke(self, **kwargs):
        self.calls.append(kwargs)
        return AdapterResult(
            success=True,
            summary="ok",
            changed_files=["backend/todos.py"],
            metadata={"structured": {"ok": True}},
        )


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


def test_workspace_lock_rejects_second_owner(tmp_path: Path) -> None:
    lock_one = WorkspaceLock(tmp_path / ".railforge" / "run.lock")
    lock_two = WorkspaceLock(tmp_path / ".railforge" / "run.lock")

    lock_one.acquire()
    try:
        with pytest.raises(WorkspaceLockError):
            lock_two.acquire()
    finally:
        lock_one.release()


def test_execution_services_forward_expected_context(tmp_path: Path) -> None:
    adapter = StubModelAdapter()
    layout = WorkspaceLayout(tmp_path)
    layout.ensure("T-001")
    task = _task()
    contract = _contract()
    run_meta = RunMeta(run_id="run-1", state=RunState.IMPLEMENTING, current_task_id="T-001")

    codex = CodexWriterService(adapter)
    backend = BackendSpecialistService(adapter)
    frontend = FrontendSpecialistService(adapter)

    codex.execute(layout=layout, task=task, contract=contract, run_meta=run_meta)
    backend.review(layout=layout, task=task, contract=contract, qa_report=None)
    frontend.review(layout=layout, task=task, contract=contract, qa_report=None)

    assert len(adapter.calls) == 3
    assert adapter.calls[0]["writable_paths"] == ["backend/", "tests/", ".railforge/tasks/T-001/"]
    assert adapter.calls[1]["writable_paths"] == [".railforge/tasks/T-001/reviews/", ".railforge/tasks/T-001/proposals/"]
