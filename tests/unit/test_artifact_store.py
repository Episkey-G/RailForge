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
        assumptions=["assumption"],
        status="ready_for_approval",
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
    store.save_product_spec(spec, draft=True)
    store.save_product_spec(spec)
    store.save_backlog("demo", "T-001", [task], draft=True)
    store.save_backlog("demo", "T-001", [task])
    store.save_task(task)
    store.save_contract(contract)
    store.save_questions({"questions": [{"id": "Q-001", "prompt": "确认规则"}]})
    store.save_answers({"answers": {"Q-001": "使用 UTC"}})
    store.save_approval("spec", approved_by="human", note="ok")

    loaded_run = store.load_run_state()
    loaded_spec = store.load_product_spec()
    backlog = store.load_backlog()
    loaded_contract = store.load_contract("T-001")

    assert loaded_run.run_id == "run-1"
    assert loaded_spec.acceptance_criteria == ["A", "B"]
    assert backlog["current_task"] == "T-001"
    assert loaded_contract.allowed_paths == ["backend/", "tests/"]
    assert layout.runtime_router.current_run_path.exists()
    assert layout.runtime_router.run_state_path("run-1").exists()
    assert layout.product_spec_draft_path.exists()
    assert layout.product_spec_path.exists()
    assert layout.backlog_draft_path.exists()
    assert layout.backlog_path.exists()
    assert store.load_answers()["answers"]["Q-001"] == "使用 UTC"
    assert store.has_approval("spec") is True


def test_checkpoint_store_saves_incremental_snapshots(tmp_path: Path) -> None:
    layout = WorkspaceLayout(tmp_path)
    store = ArtifactStore(layout)
    checkpoint_store = FileCheckpointStore(layout)
    store.init_workspace()

    run = RunMeta(run_id="run-1", state=RunState.SPEC_EXPANSION, checkpoint_index=0)
    checkpoint = checkpoint_store.save(
        run_meta=run,
        backlog={"items": []},
        current_task=None,
        langgraph_ref={"thread_id": "t-1", "checkpoint_ref": "c-1"},
    )

    assert checkpoint.sequence == 1
    assert checkpoint.path.exists()
    latest = checkpoint_store.load_latest("run-1")
    assert latest["run_state"]["state"] == "SPEC_EXPANSION"
    assert latest["langgraph"] == {"thread_id": "t-1", "checkpoint_ref": "c-1"}
