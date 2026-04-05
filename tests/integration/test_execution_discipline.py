from pathlib import Path

from railforge.adapters.base import AdapterResult, HarnessServices, LeadWriterAdapter, SpecialistAdapter
from railforge.adapters.mock import MockClarificationAnalystAdapter
from railforge.artifacts.store import ArtifactStore
from railforge.core.enums import RunState
from railforge.core.models import QaFinding, WorkspaceLayout
from railforge.integrations.git import DryRunGitAdapter
from railforge.integrations.playwright import NoopPlaywrightAdapter
from railforge.integrations.shell import LocalShellAdapter
from railforge.orchestrator.run_loop import RailForgeHarness


class BadLeadWriter(LeadWriterAdapter):
    def __init__(self) -> None:
        self.calls = 0

    def implement(self, layout, task, contract, run_meta) -> AdapterResult:
        self.calls += 1
        return AdapterResult(
            success=True,
            summary="writes outside contract scope",
            changed_files=["frontend/escape.tsx"],
            metadata={
                "runtime_status": "passed",
                "runtime_summary": "runtime verification passed",
                "outcome_status": "passed",
                "outcome_summary": "outcome checks passed",
            },
        )


class GoodLeadWriter(LeadWriterAdapter):
    def __init__(self) -> None:
        self.calls = 0

    def implement(self, layout, task, contract, run_meta) -> AdapterResult:
        self.calls += 1
        changed = task.allowed_paths[0] + "implemented.txt"
        return AdapterResult(
            success=True,
            summary="implementation complete",
            changed_files=[changed],
            metadata={
                "runtime_status": "passed",
                "runtime_summary": "runtime verification passed",
                "outcome_status": "passed",
                "outcome_summary": "outcome checks passed",
            },
        )


class CountingReviewer(SpecialistAdapter):
    def __init__(self, name: str) -> None:
        self.name = name
        self.calls = 0

    def review(self, task, qa_report, contract) -> AdapterResult:
        self.calls += 1
        return AdapterResult(success=True, summary=f"{self.name} review ok", proposed_patch="")


class FailingEvaluator:
    def __init__(self, name: str, signature: str) -> None:
        self.name = name
        self.signature = signature
        self.calls = 0

    def invoke(self, **kwargs) -> AdapterResult:
        self.calls += 1
        return AdapterResult(
            success=True,
            summary=f"{self.name} found blocking issue",
            metadata={
                "structured": {
                    "status": "failed",
                    "summary": f"{self.name} failed",
                    "findings": [
                        QaFinding(
                            severity="critical",
                            source=self.name,
                            message="blocking evaluator finding",
                            evidence="aggregate verdict should fail",
                        ).to_dict()
                    ],
                    "details": {"failure_signature": self.signature},
                }
            },
        )


class PassingEvaluator:
    def __init__(self, name: str) -> None:
        self.name = name
        self.calls = 0

    def invoke(self, **kwargs) -> AdapterResult:
        self.calls += 1
        return AdapterResult(
            success=True,
            summary=f"{self.name} ok",
            metadata={"structured": {"status": "passed", "summary": f"{self.name} passed", "findings": []}},
        )


def _services(
    *,
    lead_writer,
    backend_specialist,
    frontend_specialist,
    backend_evaluator,
    frontend_evaluator,
) -> HarnessServices:
    return HarnessServices(
        lead_writer=lead_writer,
        backend_specialist=backend_specialist,
        frontend_specialist=frontend_specialist,
        git=DryRunGitAdapter(),
        shell=LocalShellAdapter(),
        playwright=NoopPlaywrightAdapter(),
        backend_evaluator=backend_evaluator,
        frontend_evaluator=frontend_evaluator,
        clarification_analyst=MockClarificationAnalystAdapter(),
    )


def _approve_to_implementation(harness: RailForgeHarness, store: ArtifactStore) -> RunState:
    blocked = harness.run(project="todo-app", request_text="后端接口必须拒绝过去日期。")
    assert blocked.blocked_reason == "spec_approval_required"
    store.save_approval("spec", approved_by="human", note="spec ok")
    blocked = harness.resume(reason="spec_approved", note="continue")
    assert blocked.blocked_reason == "backlog_approval_required"
    store.save_approval("backlog", approved_by="human", note="backlog ok")
    store.save_approval("contract", approved_by="human", note="contract ok")
    return harness.resume(reason="contract_approved", note="continue").state


def test_deterministic_failure_short_circuits_model_review(tmp_path: Path) -> None:
    backend = CountingReviewer("backend")
    frontend = CountingReviewer("frontend")
    backend_eval = PassingEvaluator("backend_evaluator")
    frontend_eval = PassingEvaluator("frontend_evaluator")
    harness = RailForgeHarness(
        workspace=tmp_path,
        services=_services(
            lead_writer=BadLeadWriter(),
            backend_specialist=backend,
            frontend_specialist=frontend,
            backend_evaluator=backend_eval,
            frontend_evaluator=frontend_eval,
        ),
    )
    store = ArtifactStore(WorkspaceLayout(tmp_path))

    final_state = _approve_to_implementation(harness, store)

    assert final_state == RunState.BLOCKED
    assert backend.calls == 0
    assert frontend.calls == 0
    assert backend_eval.calls == 0
    assert frontend_eval.calls == 0


def test_aggregate_verdict_blocks_commit_after_evaluator_failure(tmp_path: Path) -> None:
    backend = CountingReviewer("backend")
    frontend = CountingReviewer("frontend")
    backend_eval = FailingEvaluator("backend_evaluator", "eval-backend")
    frontend_eval = PassingEvaluator("frontend_evaluator")
    lead_writer = GoodLeadWriter()
    harness = RailForgeHarness(
        workspace=tmp_path,
        services=_services(
            lead_writer=lead_writer,
            backend_specialist=backend,
            frontend_specialist=frontend,
            backend_evaluator=backend_eval,
            frontend_evaluator=frontend_eval,
        ),
    )
    store = ArtifactStore(WorkspaceLayout(tmp_path))

    final_state = _approve_to_implementation(harness, store)
    run_meta = store.load_run_state()

    assert final_state == RunState.BLOCKED
    assert backend.calls > 0
    assert frontend.calls > 0
    assert backend_eval.calls > 0
    assert frontend_eval.calls > 0
    assert run_meta.commit_log == []
    assert run_meta.blocked_reason in {"same_failure_signature", "repair_budget_exhausted", "repair_blocked", "repeated_failure_signature"}


def test_claude_provider_recovers_fenced_json_summary() -> None:
    from railforge.providers.claude_cli import ClaudeCliSpecialistAdapter

    class Wrapper:
        def run(self, **kwargs):
            return AdapterResult(
                success=True,
                summary='```json\n{"status":"passed","summary":"backend ok","findings":[],"details":{}}\n```',
                metadata={"structured": {}},
            )

    result = ClaudeCliSpecialistAdapter(wrapper=Wrapper()).invoke(role="backend_specialist", workspace="/tmp/demo", task={"id": "T-001"})

    assert result.summary == "backend ok"
    assert result.metadata["structured"]["status"] == "passed"
