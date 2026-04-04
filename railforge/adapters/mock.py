from dataclasses import dataclass
from typing import Dict, List, Optional

from railforge.adapters.base import HarnessServices, LeadWriterAdapter, SpecialistAdapter
from railforge.adapters.git import DryRunGitAdapter
from railforge.adapters.playwright import NoopPlaywrightAdapter
from railforge.adapters.shell import LocalShellAdapter
from railforge.core.models import AdapterResult, ContractSpec, QaFinding, QaReport, TaskItem, WorkspaceLayout
from railforge.guardrails.failure_signature import build_failure_signature


@dataclass
class MockAttempt:
    summary: str
    changed_files: List[str]
    writes: Dict[str, str]
    runtime_status: str
    runtime_summary: str
    runtime_findings: List[QaFinding]
    failure_signature: Optional[str]
    outcome_status: str = "passed"
    outcome_summary: str = "outcome checks passed"


def _write_files(layout: WorkspaceLayout, writes: Dict[str, str]) -> None:
    for relative, content in writes.items():
        path = layout.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


class MockLeadWriterAdapter(LeadWriterAdapter):
    def __init__(self, plans: Dict[str, List[MockAttempt]]) -> None:
        self.plans = plans
        self.attempts = {}  # type: Dict[str, int]

    def implement(self, layout: WorkspaceLayout, task: TaskItem, contract: ContractSpec, run_meta) -> AdapterResult:
        self.attempts[task.id] = self.attempts.get(task.id, 0) + 1
        plan_list = self.plans[task.id]
        index = min(self.attempts[task.id] - 1, len(plan_list) - 1)
        attempt = plan_list[index]
        _write_files(layout, attempt.writes)
        return AdapterResult(
            success=True,
            summary=attempt.summary,
            changed_files=attempt.changed_files,
            metadata={
                "runtime_status": attempt.runtime_status,
                "runtime_summary": attempt.runtime_summary,
                "runtime_findings": [finding.to_dict() for finding in attempt.runtime_findings],
                "failure_signature": attempt.failure_signature,
                "outcome_status": attempt.outcome_status,
                "outcome_summary": attempt.outcome_summary,
            },
        )


class RecoverableLeadWriterAdapter(MockLeadWriterAdapter):
    def __init__(self) -> None:
        self.recovery_allowed = False
        super(RecoverableLeadWriterAdapter, self).__init__(_default_plans())

    def allow_recovery(self) -> None:
        self.recovery_allowed = True

    def implement(self, layout: WorkspaceLayout, task: TaskItem, contract: ContractSpec, run_meta) -> AdapterResult:
        if task.id != "T-001":
            return super(RecoverableLeadWriterAdapter, self).implement(layout, task, contract, run_meta)

        self.attempts[task.id] = self.attempts.get(task.id, 0) + 1
        if self.recovery_allowed:
            attempt = _default_plans()["T-001"][1]
        else:
            attempt = _repeated_failure_attempt()
        _write_files(layout, attempt.writes)
        return AdapterResult(
            success=True,
            summary=attempt.summary,
            changed_files=attempt.changed_files,
            metadata={
                "runtime_status": attempt.runtime_status,
                "runtime_summary": attempt.runtime_summary,
                "runtime_findings": [finding.to_dict() for finding in attempt.runtime_findings],
                "failure_signature": attempt.failure_signature,
                "outcome_status": attempt.outcome_status,
                "outcome_summary": attempt.outcome_summary,
            },
        )


class MockSpecialistAdapter(SpecialistAdapter):
    def __init__(self, name: str) -> None:
        self.name = name

    def review(self, task: TaskItem, qa_report: Optional[QaReport], contract: ContractSpec) -> AdapterResult:
        if qa_report and qa_report.failure_signature:
            summary = "# %s Review for %s\n\n根因建议：上一轮失败签名为 `%s`。\n" % (
                self.name,
                task.id,
                qa_report.failure_signature,
            )
        else:
            summary = "# %s Review for %s\n\n当前变更符合 `%s` 的职责边界。\n" % (
                self.name,
                task.id,
                task.title,
            )
        return AdapterResult(
            success=True,
            summary=summary,
            proposed_patch="diff --git a/example b/example\n",
            metadata={
                "structured": {
                    "status": "passed",
                    "summary": "%s passed" % self.name,
                    "findings": [],
                }
            },
        )


def _default_plans() -> Dict[str, List[MockAttempt]]:
    failure_signature = build_failure_signature(
        failed_tests=["tests/test_due_date.py::test_rejects_past_due_date"],
        stack_excerpt="AssertionError: expected 400 got 200",
        api_error="POST_/todos_200_instead_of_400",
    )
    return {
        "T-001": [
            MockAttempt(
                summary="first backend implementation introduces timezone bug",
                changed_files=["backend/todos.py", "tests/test_due_date.py"],
                writes={
                    "backend/todos.py": "from datetime import datetime\n\n\ndef validate_due_date(value):\n    parsed = datetime.fromisoformat(value)\n    return parsed >= datetime.utcnow()\n",
                    "tests/test_due_date.py": "def test_rejects_past_due_date():\n    assert True\n",
                },
                runtime_status="failed",
                runtime_summary="pytest tests/test_due_date.py failed",
                runtime_findings=[
                    QaFinding(
                        severity="critical",
                        source="runtime",
                        message="API still accepts a past due date on timezone edge case",
                        evidence="tests/test_due_date.py::test_rejects_past_due_date",
                    )
                ],
                failure_signature=failure_signature,
                outcome_status="failed",
                outcome_summary="business outcome not satisfied",
            ),
            MockAttempt(
                summary="second backend implementation normalizes dates",
                changed_files=["backend/todos.py", "tests/test_due_date.py"],
                writes={
                    "backend/todos.py": "from datetime import datetime\n\n\ndef validate_due_date(value):\n    parsed = datetime.fromisoformat(value).date()\n    return parsed >= datetime.utcnow().date()\n",
                    "tests/test_due_date.py": "def test_rejects_past_due_date():\n    assert True\n",
                },
                runtime_status="passed",
                runtime_summary="pytest tests/test_due_date.py passed",
                runtime_findings=[],
                failure_signature=None,
            ),
        ],
        "T-002": [
            MockAttempt(
                summary="frontend inline validation implemented",
                changed_files=["frontend/TodoForm.tsx", "tests/due_date.spec.ts"],
                writes={
                    "frontend/TodoForm.tsx": "export function TodoForm(){ return 'inline validation'; }\n",
                    "tests/due_date.spec.ts": "test('shows inline validation', () => {});\n",
                },
                runtime_status="passed",
                runtime_summary="playwright due-date.spec.ts passed",
                runtime_findings=[],
                failure_signature=None,
            )
        ],
        "T-003": [
            MockAttempt(
                summary="verification coverage and regression tests updated",
                changed_files=["tests/test_regression.py", ".railforge/tasks/T-003/logs/qa.txt"],
                writes={
                    "tests/test_regression.py": "def test_regression():\n    assert True\n",
                    ".railforge/tasks/T-003/logs/qa.txt": "qa prepared\n",
                },
                runtime_status="passed",
                runtime_summary="pytest regression suite passed",
                runtime_findings=[],
                failure_signature=None,
            )
        ],
    }


def _repeated_failure_attempt() -> MockAttempt:
    signature = build_failure_signature(
        failed_tests=["tests/test_due_date.py::test_rejects_past_due_date"],
        stack_excerpt="AssertionError: expected 400 got 200",
        api_error="POST_/todos_200_instead_of_400",
    )
    return MockAttempt(
        summary="backend implementation still fails with the same bug",
        changed_files=["backend/todos.py", "tests/test_due_date.py"],
        writes={
            "backend/todos.py": "from datetime import datetime\n\n\ndef validate_due_date(value):\n    parsed = datetime.fromisoformat(value)\n    return parsed >= datetime.utcnow()\n",
            "tests/test_due_date.py": "def test_rejects_past_due_date():\n    assert True\n",
        },
        runtime_status="failed",
        runtime_summary="pytest tests/test_due_date.py failed",
        runtime_findings=[
            QaFinding(
                severity="critical",
                source="runtime",
                message="API still accepts a past due date on timezone edge case",
                evidence="tests/test_due_date.py::test_rejects_past_due_date",
            )
        ],
        failure_signature=signature,
        outcome_status="failed",
        outcome_summary="business outcome not satisfied",
    )


def build_default_mock_services() -> HarnessServices:
    return HarnessServices(
        lead_writer=MockLeadWriterAdapter(_default_plans()),
        backend_specialist=MockSpecialistAdapter("Backend"),
        frontend_specialist=MockSpecialistAdapter("Frontend"),
        git=DryRunGitAdapter(),
        shell=LocalShellAdapter(),
        playwright=NoopPlaywrightAdapter(),
        backend_evaluator=MockSpecialistAdapter("Backend Evaluator"),
        frontend_evaluator=MockSpecialistAdapter("Frontend Evaluator"),
    )


class RecoverableMockServices(object):
    def __init__(self) -> None:
        self.lead_writer = RecoverableLeadWriterAdapter()
        self.backend_specialist = MockSpecialistAdapter("Backend")
        self.frontend_specialist = MockSpecialistAdapter("Frontend")
        self.backend_evaluator = MockSpecialistAdapter("Backend Evaluator")
        self.frontend_evaluator = MockSpecialistAdapter("Frontend Evaluator")
        self.git = DryRunGitAdapter()
        self.shell = LocalShellAdapter()
        self.playwright = NoopPlaywrightAdapter()

    def allow_recovery(self) -> None:
        self.lead_writer.allow_recovery()


def build_repeated_failure_services() -> RecoverableMockServices:
    return RecoverableMockServices()
