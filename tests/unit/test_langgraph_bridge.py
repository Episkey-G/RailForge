from pathlib import Path

from railforge.core.enums import RunState
from railforge.core.models import RunMeta, WorkspaceLayout
from railforge.infra.checkpoint_store import FileCheckpointStore
from railforge.infra.langgraph_bridge import LangGraphBridge


def test_langgraph_bridge_returns_thread_and_checkpoint_refs() -> None:
    bridge = LangGraphBridge()

    ref = bridge.record(run_id="run-1", state="SPEC_EXPANSION", payload={"items": []})

    assert ref["thread_id"].startswith("lg-thread-run-1")
    assert ref["checkpoint_ref"]


def test_file_checkpoint_store_persists_langgraph_refs(tmp_path: Path) -> None:
    layout = WorkspaceLayout(tmp_path)
    layout.ensure()
    store = FileCheckpointStore(layout)
    run = RunMeta(run_id="run-1", state=RunState.INTAKE)

    store.save(
        run_meta=run,
        backlog={"items": []},
        current_task=None,
        langgraph_ref={"thread_id": "t-1", "checkpoint_ref": "c-1"},
    )

    latest = store.load_latest()
    assert latest["langgraph"]["thread_id"] == "t-1"
    assert latest["langgraph"]["checkpoint_ref"] == "c-1"
