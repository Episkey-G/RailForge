from railforge.core.models import PhaseEvaluationResult, QaFinding, TaskItem
from railforge.evaluator.aggregate_eval import AggregateEvaluator
from railforge.evaluator.qa_manager import QaManager


def _task() -> TaskItem:
    return TaskItem(
        id="T-001",
        title="Dual evaluation",
        status="ready",
        priority="high",
        depends_on=[],
        allowed_paths=["railforge/", "tests/"],
        verification=["pytest tests/unit/test_dual_evaluator.py"],
        repair_budget=3,
        done_definition=["merge backend and frontend verdicts"],
    )


def _phase(status: str = "passed", summary: str = "ok", findings=None, details=None) -> PhaseEvaluationResult:
    return PhaseEvaluationResult(
        status=status,
        summary=summary,
        findings=list(findings or []),
        details=dict(details or {}),
    )


def test_aggregate_eval_fails_on_critical_finding() -> None:
    verdict = AggregateEvaluator().merge(
        backend_status={
            "status": "passed",
            "summary": "backend ok",
            "findings": [
                QaFinding(
                    severity="critical",
                    source="backend",
                    message="missing transaction guard",
                    evidence="railforge/api.py",
                ).to_dict()
            ],
        },
        frontend_status=_phase(summary="frontend ok"),
    )

    assert verdict.status == "failed"
    assert verdict.findings[0].severity == "critical"
    assert verdict.details["critical_finding"]["message"] == "missing transaction guard"


def test_aggregate_eval_fails_when_either_evaluator_fails() -> None:
    verdict = AggregateEvaluator().merge(
        backend_status=_phase(status="failed", summary="backend failed"),
        frontend_status={"status": "passed", "summary": "frontend ok", "findings": []},
    )

    assert verdict.status == "failed"
    assert verdict.details["backend"]["status"] == "failed"
    assert verdict.details["frontend"]["status"] == "passed"


def test_qa_manager_build_dual_report_approves_when_both_pass() -> None:
    report = QaManager().build_dual_report(
        task=_task(),
        backend_status={"status": "passed", "summary": "backend ok", "findings": []},
        frontend_status=_phase(status="passed", summary="frontend ok"),
    )

    assert report.status == "approved"
    assert report.static == {"status": "passed", "summary": "backend ok"}
    assert report.runtime == {"status": "passed", "summary": "frontend ok"}
    assert report.outcome == {"status": "passed", "summary": "backend and frontend evaluators passed"}
    assert report.findings == []
