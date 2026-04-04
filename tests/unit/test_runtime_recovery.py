from pathlib import Path

from railforge.artifacts.store import ArtifactStore
from railforge.core.enums import RunState
from railforge.core.models import RunMeta, TaskItem, WorkspaceLayout
from railforge.infra.checkpoint_store import FileCheckpointStore
from railforge.infra.langgraph_bridge import LangGraphBridge
from railforge.infra.runtime_recovery import RuntimeRecovery


def _task(task_id: str = "T-001", status: str = "in_progress") -> TaskItem:
    return TaskItem(
        id=task_id,
        title="持久化恢复",
        status=status,
        priority="high",
        depends_on=[],
        allowed_paths=["railforge/infra/", "tests/"],
        verification=["pytest tests/unit/test_runtime_recovery.py"],
        repair_budget=2,
        done_definition=["恢复当前任务上下文"],
    )


def test_runtime_recovery_prefers_file_truth_over_stale_checkpoint(tmp_path: Path) -> None:
    layout = WorkspaceLayout(tmp_path)
    store = ArtifactStore(layout)
    checkpoint_store = FileCheckpointStore(layout)
    store.init_workspace()

    run = RunMeta(
        run_id="run-1",
        state=RunState.BLOCKED,
        current_task_id="T-001",
        blocked_reason="hosted_execution_required",
        resume_from_state="IMPLEMENTING",
    )
    task = _task()
    store.save_run_state(run)
    store.save_task(task)
    store.save_backlog("demo", "T-001", [task])
    checkpoint_store.save(
        run_meta=RunMeta(run_id="run-1", state=RunState.DONE),
        backlog={"project": "demo", "current_task": None, "items": []},
        current_task=None,
        langgraph_ref={"thread_id": "stale-thread", "checkpoint_ref": "stale-checkpoint"},
        git_state={"available": False, "dirty": False, "head": None, "branch": None, "status": []},
    )

    snapshot = RuntimeRecovery(
        layout=layout,
        store=store,
        checkpoints=checkpoint_store,
        langgraph=LangGraphBridge(layout),
    ).recover()

    assert snapshot.run_meta.state == RunState.BLOCKED
    assert snapshot.run_meta.current_task_id == "T-001"
    assert snapshot.checkpoint_consistent is False
    assert "checkpoint_mismatch" in snapshot.issues


def test_runtime_recovery_rehydrates_current_task_from_backlog(tmp_path: Path) -> None:
    layout = WorkspaceLayout(tmp_path)
    store = ArtifactStore(layout)
    checkpoint_store = FileCheckpointStore(layout)
    store.init_workspace()

    run = RunMeta(
        run_id="run-1",
        state=RunState.BLOCKED,
        current_task_id=None,
        blocked_reason="hosted_execution_required",
        resume_from_state="IMPLEMENTING",
    )
    task = _task()
    store.save_run_state(run)
    store.save_task(task)
    store.save_backlog("demo", "T-001", [task])

    snapshot = RuntimeRecovery(
        layout=layout,
        store=store,
        checkpoints=checkpoint_store,
        langgraph=LangGraphBridge(layout),
    ).recover()

    assert snapshot.run_meta.current_task_id == "T-001"
    assert snapshot.current_task.id == "T-001"


def test_runtime_recovery_marks_failed_when_truth_cannot_be_rebuilt(tmp_path: Path) -> None:
    layout = WorkspaceLayout(tmp_path)
    store = ArtifactStore(layout)
    checkpoint_store = FileCheckpointStore(layout)
    store.init_workspace()

    run = RunMeta(
        run_id="run-1",
        state=RunState.BLOCKED,
        current_task_id="T-404",
        blocked_reason="hosted_execution_required",
        resume_from_state="IMPLEMENTING",
    )
    store.save_run_state(run)
    store.save_backlog("demo", None, [])

    snapshot = RuntimeRecovery(
        layout=layout,
        store=store,
        checkpoints=checkpoint_store,
        langgraph=LangGraphBridge(layout),
    ).recover()

    assert snapshot.run_meta.state == RunState.FAILED
    assert snapshot.failure_reason == "current_task_missing"
