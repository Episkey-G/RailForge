from pathlib import Path

from railforge.core.enums import RunState
from railforge.core.models import RunMeta, WorkspaceLayout
from railforge.application.phase_context import build_phase_context
from railforge.artifacts.store import ArtifactStore


def test_phase_context_exposes_planning_truth_and_contract_gate(tmp_path: Path) -> None:
    layout = WorkspaceLayout(tmp_path)
    store = ArtifactStore(layout)
    store.init_workspace()
    store.write_yaml(
        layout.planning_contract_path,
        {
            "change": "demo",
            "status": "awaiting_approval",
            "write_scope": {"allowed_paths": ["backend/**"]},
            "deliverables": ["backend delivery"],
            "locked_decisions": ["keep repo clean"],
        },
    )
    store.save_run_state(RunMeta(run_id="run-1", state=RunState.BACKLOG_BUILD))
    store.save_approval("backlog", approved_by="human", note="ok")

    payload = build_phase_context(tmp_path, phase="spec-impl")

    assert payload["planning_contract"]["status"] == "awaiting_approval"
    assert payload["contract_gate"]["approval_required"] is True
    assert payload["contract_gate"]["source"] == "docs"
    assert payload["paths"]["planning_contract_truth"] == "docs/exec-plans/active/contract.yaml"
    assert "docs/exec-plans/active/contract.yaml" in payload["sources"]["docs_truth"]
