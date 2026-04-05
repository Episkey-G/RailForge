import json

from railforge.artifacts.store import ArtifactStore
from railforge.core.enums import RunState
from railforge.core.models import QaReport, RunMeta, WorkspaceLayout
from railforge.observability.ledger import classify_failure, ObservabilityLedger


def test_classify_failure_uses_blueprint_categories() -> None:
    assert classify_failure("spec_approval_required").category == "spec_defect"
    assert classify_failure("review_context_missing").category == "workflow_skill_defect"
    assert classify_failure("current_task_missing").category == "context_assembly_defect"
    assert classify_failure("hosted_execution_required").category == "provider_tool_fault"
    assert classify_failure("unexpected_gate").category == "deterministic_gate_gap"


def test_observability_ledger_writes_run_scoped_verdict(tmp_path) -> None:
    layout = WorkspaceLayout(tmp_path)
    store = ArtifactStore(layout)
    store.init_workspace()
    store.save_run_state(RunMeta(run_id="run-1", state=RunState.RUNTIME_QA, current_task_id="T-001"))
    ledger = ObservabilityLedger(layout, store)

    qa = QaReport(
        task_id="T-001",
        status="failed",
        static={"status": "passed", "summary": "ok"},
        runtime={"status": "passed", "summary": "ok"},
        outcome={"status": "failed", "summary": "aggregate failed"},
        findings=[],
        failure_signature="sig-1",
        review={"mode": "runtime_qa", "status": "failed"},
        backend={"status": "failed"},
        frontend={"status": "passed"},
    )
    ledger.record_qa_report(qa)

    verdict = json.loads((layout.ledgers_dir / "run-1.latest_verdict.json").read_text(encoding="utf-8"))
    assert verdict["task_id"] == "T-001"
    assert verdict["quality_grade"] == "C"
    assert verdict["review"]["mode"] == "runtime_qa"
    assert (layout.ledgers_dir / "run-1.jsonl").exists()
