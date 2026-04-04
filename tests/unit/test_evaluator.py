from railforge.core.models import AdapterResult, ContractSpec, QaFinding, TaskItem
from railforge.evaluator.qa_manager import QaManager
from railforge.evaluator.static_eval import StaticEvaluator


def _task() -> TaskItem:
    return TaskItem(
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


def test_static_evaluator_rejects_out_of_scope_change() -> None:
    report = StaticEvaluator().evaluate(
        task=_task(),
        contract=_contract(),
        implementation=AdapterResult(
            success=True,
            summary="changed files",
            changed_files=["backend/todos.py", "frontend/form.tsx"],
        ),
        reviews=[],
    )
    assert report.status == "failed"
    assert any("allowed_paths" in finding.message for finding in report.findings)


def test_qa_manager_approves_green_result() -> None:
    report = QaManager().build_report(
        task=_task(),
        static_status={"status": "passed", "summary": "ok"},
        runtime_status={"status": "passed", "summary": "ok"},
        outcome_status={"status": "passed", "summary": "ok"},
        findings=[],
        failure_signature=None,
    )
    assert report.status == "approved"


def test_qa_manager_fails_when_findings_exist() -> None:
    report = QaManager().build_report(
        task=_task(),
        static_status={"status": "passed", "summary": "ok"},
        runtime_status={"status": "failed", "summary": "fail"},
        outcome_status={"status": "passed", "summary": "ok"},
        findings=[QaFinding(severity="critical", source="runtime", message="boom", evidence="test")],
        failure_signature="sig",
    )
    assert report.status == "failed"
    assert report.failure_signature == "sig"
