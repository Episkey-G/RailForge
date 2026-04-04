from pathlib import Path

from railforge.artifacts.store import ArtifactStore
from railforge.core.enums import RunState
from railforge.core.models import ContractSpec, ProductSpec, RunMeta, TaskItem, WorkspaceLayout
from railforge.infra.checkpoint_store import FileCheckpointStore


def test_artifact_store_roundtrip(tmp_path: Path) -> None:
    layout = WorkspaceLayout(tmp_path)
    store = ArtifactStore(layout)
    store.init_workspace()

    run = RunMeta(run_id="run-1", state=RunState.INTAKE)
    spec = ProductSpec(
        title="Demo",
        summary="Summary",
        acceptance_criteria=["A", "B"],
        constraints=["C"],
    )
    task = TaskItem(
        id="T-001",
        title="Backend validation",
        status="ready",
        priority="high",
        depends_on=[],
        allowed_paths=["backend/", "tests/"],
        verification=["pytest tests/test_demo.py"],
        repair_budget=3,
        done_definition=["reject invalid input"],
    )
    contract = ContractSpec(
        task_id="T-001",
        scope=["backend validation"],
        non_scope=["frontend refresh"],
        allowed_paths=["backend/", "tests/"],
        verification=["pytest tests/test_demo.py"],
        rollback=["revert backend validator"],
        done_definition=["reject invalid input"],
    )

    store.save_run_state(run)
    store.save_product_spec(spec)
    store.save_backlog("demo", "T-001", [task])
    store.save_task(task)
    store.save_contract(contract)

    loaded_run = store.load_run_state()
    loaded_spec = store.load_product_spec()
    backlog = store.load_backlog()
    loaded_contract = store.load_contract("T-001")

    assert loaded_run.run_id == "run-1"
    assert loaded_spec.acceptance_criteria == ["A", "B"]
    assert backlog["current_task"] == "T-001"
    assert loaded_contract.allowed_paths == ["backend/", "tests/"]


def test_checkpoint_store_saves_incremental_snapshots(tmp_path: Path) -> None:
    layout = WorkspaceLayout(tmp_path)
    store = ArtifactStore(layout)
    checkpoint_store = FileCheckpointStore(layout)
    store.init_workspace()

    run = RunMeta(run_id="run-1", state=RunState.SPEC_EXPANSION, checkpoint_index=0)
    checkpoint = checkpoint_store.save(run_meta=run, backlog={"items": []}, current_task=None)

    assert checkpoint.sequence == 1
    assert checkpoint.path.exists()
    latest = checkpoint_store.load_latest()
    assert latest["run_state"]["state"] == "SPEC_EXPANSION"
