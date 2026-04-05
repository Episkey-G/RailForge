from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from railforge.adapters.base import HarnessServices
from railforge.artifacts.store import ArtifactStore
from railforge.core.enums import RunState
from railforge.core.errors import ArtifactNotFoundError, ResumeError
from railforge.core.fsm import ensure_transition, terminal_states
from railforge.core.models import (
    AdapterResult,
    ContractSpec,
    PhaseEvaluationResult,
    QaReport,
    RunMeta,
    TaskItem,
    WorkspaceLayout,
)
from railforge.evaluator.aggregate_eval import AggregateEvaluator, coerce_phase_result
from railforge.evaluator.outcome_eval import OutcomeEvaluator
from railforge.evaluator.qa_manager import QaManager
from railforge.evaluator.runtime_eval import RuntimeEvaluator
from railforge.evaluator.static_eval import StaticEvaluator
from railforge.execution.backend_specialist import BackendSpecialistService
from railforge.execution.codex_writer import CodexWriterService
from railforge.execution.frontend_specialist import FrontendSpecialistService
from railforge.guardrails.budgets import repair_decision
from railforge.infra.checkpoint_store import FileCheckpointStore
from railforge.infra.file_lock import WorkspaceLock
from railforge.infra.langgraph_bridge import LangGraphBridge
from railforge.infra.runtime_recovery import RuntimeRecovery
from railforge.infra.run_logger import RunLogger
from railforge.planner.backlog_builder import build_backlog
from railforge.planner.clarification import analyze_request
from railforge.planner.contract_builder import build_contract
from railforge.planner.planning_contract import load_planning_contract
from railforge.planner.task_selector import select_next_task

from .commit_gate import evaluate_commit_gate
from .contract_gate import ContractGate
from .interrupts import InterruptManager


class RailForgeHarness:
    def __init__(self, workspace: Path, services: HarnessServices) -> None:
        self.layout = WorkspaceLayout(Path(workspace))
        self.store = ArtifactStore(self.layout)
        self.checkpoints = FileCheckpointStore(self.layout)
        self.logger = RunLogger(self.store)
        self.services = services
        self.lock = WorkspaceLock(self.layout.rf / "run.lock")
        self.contract_gate = ContractGate()
        self.interrupts = InterruptManager(self.layout)
        self.langgraph = LangGraphBridge(self.layout)
        self.runtime_recovery = RuntimeRecovery(
            layout=self.layout,
            store=self.store,
            checkpoints=self.checkpoints,
            langgraph=self.langgraph,
            git_adapter=self.services.git,
        )
        self.aggregate_evaluator = AggregateEvaluator()
        self.static_evaluator = StaticEvaluator()
        self.runtime_evaluator = RuntimeEvaluator()
        self.outcome_evaluator = OutcomeEvaluator()
        self.qa_manager = QaManager()
        self.codex_writer = CodexWriterService(self.services.lead_writer)
        self.backend_specialist = BackendSpecialistService(self.services.backend_specialist)
        self.frontend_specialist = FrontendSpecialistService(self.services.frontend_specialist)
        self.run_meta: Optional[RunMeta] = None
        self._last_implementation: Optional[AdapterResult] = None
        self._last_static: Optional[PhaseEvaluationResult] = None
        self._last_reviews: List[AdapterResult] = []

    @staticmethod
    def _severity_counts(findings: List[Any]) -> Dict[str, int]:
        counts = {"critical": 0, "warning": 0, "info": 0}
        for finding in findings:
            severity = getattr(finding, "severity", "")
            if severity == "critical":
                counts["critical"] += 1
            elif severity in {"high", "medium", "warning"}:
                counts["warning"] += 1
            else:
                counts["info"] += 1
        return counts

    @staticmethod
    def _merge_findings(*groups: List[Any]) -> List[Any]:
        merged: List[Any] = []
        seen = set()
        for group in groups:
            for finding in group:
                key = (
                    getattr(finding, "severity", None),
                    getattr(finding, "source", None),
                    getattr(finding, "message", None),
                    getattr(finding, "evidence", None),
                )
                if key in seen:
                    continue
                seen.add(key)
                merged.append(finding)
        return merged

    def _build_review_summary(
        self,
        *,
        mode: str,
        scope: str,
        status: str,
        summary: str,
        findings: List[Any],
        failure_signature: Optional[str],
        next_action: str,
    ) -> Dict[str, Any]:
        return {
            "mode": mode,
            "scope": scope,
            "status": status,
            "summary": summary,
            "severity_counts": self._severity_counts(findings),
            "failure_signature": failure_signature,
            "next_action": next_action,
        }

    def _write_task_review_markdown(
        self,
        task: TaskItem,
        *,
        file_name: str,
        backend_phase: PhaseEvaluationResult,
        frontend_phase: PhaseEvaluationResult,
        review_summary: Dict[str, Any],
    ) -> None:
        lines = [
            "# Spec Review - %s" % task.id,
            "",
            "## Aggregate",
            "- Status: %s" % review_summary["status"],
            "- Summary: %s" % review_summary["summary"],
            "- Next Action: %s" % review_summary["next_action"],
            "",
            "## Severity Counts",
            "- Critical: %s" % review_summary["severity_counts"]["critical"],
            "- Warning: %s" % review_summary["severity_counts"]["warning"],
            "- Info: %s" % review_summary["severity_counts"]["info"],
            "",
            "## Backend Evaluator",
            "- Status: %s" % backend_phase.status,
            "- Summary: %s" % backend_phase.summary,
            "",
            "## Frontend Evaluator",
            "- Status: %s" % frontend_phase.status,
            "- Summary: %s" % frontend_phase.summary,
        ]
        self.store.save_review(task.id, file_name, "\n".join(lines) + "\n")

    def _persist_dual_evaluation_artifacts(
        self,
        task: TaskItem,
        *,
        backend_phase: PhaseEvaluationResult,
        frontend_phase: PhaseEvaluationResult,
        aggregate_phase: PhaseEvaluationResult,
        review_summary: Dict[str, Any],
    ) -> None:
        mode = review_summary["mode"]
        self.store.save_review(task.id, "backend_evaluator.md", backend_phase.summary + "\n")
        self.store.save_review(task.id, "frontend_evaluator.md", frontend_phase.summary + "\n")
        self.store.write_json(
            self.layout.task_reviews_dir(task.id) / ("%s.json" % mode),
            {
                "mode": mode,
                "task_id": task.id,
                "aggregate": review_summary,
            },
        )
        self._write_task_review_markdown(
            task,
            file_name="%s.md" % mode,
            backend_phase=backend_phase,
            frontend_phase=frontend_phase,
            review_summary=review_summary,
        )
        self.store.save_trace(
            task.id,
            "backend_evaluator.json",
            {
                "status": backend_phase.status,
                "summary": backend_phase.summary,
                "findings": [finding.to_dict() for finding in backend_phase.findings],
                "details": backend_phase.details,
            },
        )
        self.store.save_trace(
            task.id,
            "frontend_evaluator.json",
            {
                "status": frontend_phase.status,
                "summary": frontend_phase.summary,
                "findings": [finding.to_dict() for finding in frontend_phase.findings],
                "details": frontend_phase.details,
            },
        )
        self.store.save_trace(
            task.id,
            "aggregate_evaluator.json",
            {
                "status": aggregate_phase.status,
                "summary": aggregate_phase.summary,
                "findings": [finding.to_dict() for finding in aggregate_phase.findings],
                "details": aggregate_phase.details,
                "review": review_summary,
            },
        )

    def _write_final_review(self, payload: Dict[str, Any]) -> None:
        lines = [
            "# Final Review",
            "",
            "- Status: %s" % payload["status"],
            "- Summary: %s" % payload["summary"],
            "- Approved Tasks: %s/%s" % (payload["approved_tasks"], payload["total_tasks"]),
            "- Next Action: %s" % payload["next_action"],
        ]
        self.store.write_json(self.layout.final_review_path, payload)
        self.store.write_text(self.layout.final_review_markdown_path, "\n".join(lines) + "\n")

    def _build_final_review_payload(self, tasks: List[TaskItem]) -> Dict[str, Any]:
        task_results = []
        findings: List[Any] = []
        verification_commands: List[str] = []
        approved_tasks = 0
        failed_tasks: List[str] = []
        missing_reports: List[str] = []

        for task in tasks:
            verification_commands.extend(task.verification)
            try:
                qa_report = self.store.load_qa_report(task.id)
            except ArtifactNotFoundError:
                missing_reports.append(task.id)
                task_results.append({"task_id": task.id, "status": "missing_qa_report"})
                continue
            findings = self._merge_findings(findings, qa_report.findings)
            task_results.append({"task_id": task.id, "status": qa_report.status})
            if qa_report.status == "approved":
                approved_tasks += 1
            else:
                failed_tasks.append(task.id)

        status = "approved" if approved_tasks == len(tasks) and not missing_reports and not failed_tasks else "failed"
        next_action = "openspec-archive-change" if status == "approved" else "rf-spec-review"
        summary = "all task-level QA gates approved" if status == "approved" else "change-level verification found unresolved tasks"

        payload = {
            "mode": "spec_review",
            "scope": "change",
            "project": self.run_meta.project_name if self.run_meta else "",
            "status": status,
            "summary": summary,
            "approved_tasks": approved_tasks,
            "total_tasks": len(tasks),
            "failed_tasks": failed_tasks,
            "missing_reports": missing_reports,
            "verification_commands": verification_commands,
            "commit_count": len(self.run_meta.commit_log) if self.run_meta else 0,
            "tasks": task_results,
            "severity_counts": self._severity_counts(findings),
            "next_action": next_action,
        }
        self._write_final_review(payload)
        return payload

    def run_spec_review(self) -> Dict[str, Any]:
        self.store.init_workspace()
        try:
            self._recover_runtime()
        except ResumeError:
            try:
                self.run_meta = self.store.load_run_state()
            except ArtifactNotFoundError:
                return {
                    "mode": "spec_review",
                    "status": "failed",
                    "reason": "review_context_missing",
                }

        tasks = self._load_tasks()
        if not tasks:
            return {
                "mode": "spec_review",
                "status": "failed",
                "reason": "review_context_missing",
            }

        if all(task.status == "done" for task in tasks):
            return self._build_final_review_payload(tasks)

        task_id = self.run_meta.current_task_id or next((task.id for task in tasks if task.status == "in_progress"), None)
        if not task_id:
            task_id = next((task.id for task in tasks if task.status == "done"), None)
        if not task_id:
            return {
                "mode": "spec_review",
                "status": "failed",
                "reason": "task_context_missing",
            }

        task = self.store.load_task(task_id)
        contract = self.store.load_contract(task_id)
        try:
            qa_report = self.store.load_qa_report(task_id)
        except ArtifactNotFoundError:
            return {
                "mode": "spec_review",
                "scope": "task",
                "task_id": task_id,
                "status": "failed",
                "reason": "qa_report_missing",
            }

        backend_eval = self._invoke_phase_adapter(
            getattr(self.services, "backend_evaluator", None),
            "backend_evaluator",
            task,
            contract,
            qa_report,
        )
        frontend_eval = self._invoke_phase_adapter(
            getattr(self.services, "frontend_evaluator", None),
            "frontend_evaluator",
            task,
            contract,
            qa_report,
        )
        aggregate_phase = self.aggregate_evaluator.merge(backend_eval, frontend_eval)
        combined_findings = self._merge_findings(qa_report.findings, aggregate_phase.findings)
        status = "approved" if qa_report.status == "approved" and aggregate_phase.status == "passed" else "failed"
        review_summary = self._build_review_summary(
            mode="spec_review",
            scope="task",
            status=status,
            summary=aggregate_phase.summary if status == "failed" else "independent spec review passed",
            findings=combined_findings,
            failure_signature=qa_report.failure_signature or aggregate_phase.details.get("failure_signature"),
            next_action="rf-spec-impl" if status == "failed" else "openspec-archive-change",
        )
        updated_report = QaReport(
            task_id=qa_report.task_id,
            status=status,
            static=qa_report.static,
            runtime=qa_report.runtime,
            outcome=qa_report.outcome,
            findings=combined_findings,
            failure_signature=qa_report.failure_signature or aggregate_phase.details.get("failure_signature"),
            confidence_score=1.0 if status == "approved" else 0.35,
            backend=aggregate_phase.details.get("backend", {}),
            frontend=aggregate_phase.details.get("frontend", {}),
            review=review_summary,
        )
        self._persist_dual_evaluation_artifacts(
            task,
            backend_phase=backend_eval,
            frontend_phase=frontend_eval,
            aggregate_phase=aggregate_phase,
            review_summary=review_summary,
        )
        self.store.save_qa_report(task.id, updated_report)
        payload = {
            "mode": "spec_review",
            "scope": "task",
            "project": self.run_meta.project_name if self.run_meta else "",
            "task_id": task.id,
            "status": status,
            "aggregate": review_summary,
            "qa_report": updated_report.to_dict(),
        }
        self.store.write_json(self.layout.task_reviews_dir(task.id) / "spec_review.json", payload)
        return payload

    def run(self, project: str, request_text: str) -> RunMeta:
        self.store.init_workspace()
        with self.lock:
            self.run_meta = RunMeta(
                run_id="run-%s" % uuid4().hex[:8],
                state=RunState.INTAKE,
                project_name=project,
                request_text=request_text,
            )
            self.store.save_run_state(self.run_meta)
            self._snapshot()
            return self._drive()

    def resume(self, reason: str, note: str) -> RunMeta:
        self.store.init_workspace()
        with self.lock:
            self._recover_runtime()
            if self.run_meta.state != RunState.BLOCKED:
                raise ResumeError("run is not blocked")
            if not self.run_meta.resume_from_state:
                raise ResumeError("blocked run has no resume_from_state")
            self.interrupts.record_unblock(reason=reason, note=note)
            self.interrupts.clear_blocked()
            self.run_meta.state = RunState(self.run_meta.resume_from_state)
            self.run_meta.blocked_reason = None
            self.run_meta.repair_count = 0
            self.run_meta.last_failure_signature = None
            self.store.save_run_state(self.run_meta)
            self._snapshot()
            return self._drive()

    def execute_current_task(self) -> RunMeta:
        self.store.init_workspace()
        with self.lock:
            self._recover_runtime()
            return self._drive()

    def prepare_execution_payload(self, reason: str, note: str) -> Dict[str, Any]:
        self.store.init_workspace()
        with self.lock:
            self._recover_runtime()
            if self.run_meta.state == RunState.BLOCKED and self.run_meta.resume_from_state:
                self.interrupts.record_unblock(reason=reason, note=note)
                self.interrupts.clear_blocked()
                self.run_meta.state = RunState(self.run_meta.resume_from_state)
                self.run_meta.blocked_reason = None
                self.run_meta.last_failure_signature = None
                self.store.save_run_state(self.run_meta)
                self._snapshot()
            result = self._drive()
            if result.blocked_reason != "hosted_execution_required":
                raise ResumeError("run is not waiting for hosted execution")
            payload = self.store.read_json(self.layout.hosted_execution_request_path)
            task_id = payload.get("task_id") or self.run_meta.current_task_id
            if task_id:
                self.store.save_trace(task_id, "hosted_execution_request.json", payload)
            return payload

    def record_execution_result(self, payload: Dict[str, Any]) -> RunMeta:
        self.store.init_workspace()
        with self.lock:
            self._recover_runtime()
            if self.run_meta.blocked_reason != "hosted_execution_required":
                raise ResumeError("run is not waiting for hosted execution result")
            task_id = self.run_meta.current_task_id or payload.get("task_id")
            if not task_id:
                raise ResumeError("hosted execution result missing task id")
            self.run_meta.current_task_id = task_id
            self.store.write_json(self.layout.hosted_execution_result_path, payload)
            self.store.save_trace(task_id, "hosted_execution_result.json", payload)
            self._last_implementation = AdapterResult(
                success=True,
                summary=payload["summary"],
                changed_files=payload.get("changed_files", []),
                metadata={
                    "mode": "hosted_codex",
                    "recorded": True,
                    "runtime_status": "passed",
                    "runtime_summary": "hosted execution reported verification success",
                    "verification_notes": payload.get("verification_notes", []),
                },
            )
            self.run_meta.state = RunState.STATIC_REVIEW
            self.run_meta.blocked_reason = None
            self.run_meta.resume_from_state = None
            self.interrupts.clear_blocked()
            self.store.save_run_state(self.run_meta)
            self._snapshot()
            return self._drive()

    def _drive(self) -> RunMeta:
        while self.run_meta and self.run_meta.state not in terminal_states():
            state = self.run_meta.state
            if state == RunState.INTAKE:
                self._handle_intake()
            elif state == RunState.SPEC_EXPANSION:
                self._handle_spec_expansion()
            elif state == RunState.BACKLOG_BUILD:
                self._handle_backlog_build()
            elif state == RunState.TASK_SELECTED:
                self._handle_task_selected()
            elif state == RunState.CONTRACT_NEGOTIATION:
                self._handle_contract_negotiation()
            elif state == RunState.IMPLEMENTING:
                self._handle_implementing()
            elif state == RunState.STATIC_REVIEW:
                self._handle_static_review()
            elif state == RunState.RUNTIME_QA:
                self._handle_runtime_qa()
            elif state == RunState.REPAIRING:
                self._handle_repairing()
            elif state == RunState.READY_TO_COMMIT:
                self._handle_ready_to_commit()
            elif state == RunState.COMMITTED:
                self._handle_committed()
            elif state == RunState.NEXT_TASK:
                self._handle_next_task()
        return self.run_meta

    def _transition(self, nxt: RunState) -> None:
        ensure_transition(self.run_meta.state, nxt)
        self.run_meta.state = nxt
        if nxt != RunState.BLOCKED:
            self.run_meta.blocked_reason = None
            self.run_meta.resume_from_state = None
            self.interrupts.clear_blocked()
        self.store.save_run_state(self.run_meta)
        self.logger.append("STATE -> %s" % nxt.value)
        self._snapshot()

    def _active_backlog(self) -> Dict[str, Any]:
        if self.layout.backlog_path.exists():
            return self.store.load_backlog()
        if self.layout.backlog_draft_path.exists():
            return self.store.load_backlog(draft=True)
        return {"items": []}

    def _load_answers(self) -> Dict[str, str]:
        try:
            payload = self.store.load_answers()
        except ArtifactNotFoundError:
            return {}
        return payload.get("answers", {})

    def _has_approval(self, target: str, task_id: str = "") -> bool:
        return self.store.has_approval(target=target, task_id=task_id)

    def _block(self, reason: str, resume_from_state: RunState, note: str, task_id: str = "PLANNING") -> None:
        self.run_meta.blocked_reason = reason
        self.run_meta.resume_from_state = resume_from_state.value
        self.interrupts.record_blocked(
            task_id=task_id,
            reason=reason,
            resume_from_state=resume_from_state.value,
            note=note,
        )
        self.store.save_run_state(self.run_meta)
        self._transition(RunState.BLOCKED)

    def _snapshot(self) -> None:
        current_task = None
        backlog = self._active_backlog()
        if self.run_meta and self.run_meta.current_task_id:
            task_path = self.layout.task_dir(self.run_meta.current_task_id) / "task.yaml"
            if task_path.exists():
                current_task = self.store.load_task(self.run_meta.current_task_id)
        lg_ref = self.langgraph.record(
            run_id=self.run_meta.run_id,
            state=self.run_meta.state.value,
            payload={"backlog": backlog, "current_task_id": self.run_meta.current_task_id},
        )
        self.run_meta.thread_id = lg_ref["thread_id"]
        self.run_meta.checkpoint_ref = lg_ref["checkpoint_ref"]
        checkpoint = self.checkpoints.save(
            self.run_meta,
            backlog,
            current_task,
            langgraph_ref=lg_ref,
            git_state=self.runtime_recovery.inspect_git_state(),
        )
        self.run_meta.checkpoint_index = checkpoint.sequence
        self.store.save_run_state(self.run_meta)

    def _recover_runtime(self) -> None:
        snapshot = self.runtime_recovery.recover()
        if snapshot.run_meta is None:
            raise ResumeError(snapshot.failure_reason or "run_state missing")
        self.run_meta = snapshot.run_meta
        if snapshot.current_task is not None:
            self.store.save_task(snapshot.current_task)
        if self.run_meta.state != RunState.BLOCKED:
            self.interrupts.clear_blocked()
        self.store.save_run_state(self.run_meta)
        if self.run_meta.state == RunState.FAILED:
            raise ResumeError(snapshot.failure_reason or "runtime recovery failed")

    def _load_tasks(self) -> List[TaskItem]:
        backlog = self._active_backlog()
        return [TaskItem.from_dict(item) for item in backlog.get("items", [])]

    def _persist_tasks(self, tasks: List[TaskItem], current_task: Optional[str], draft: bool = False) -> None:
        for task in tasks:
            self.store.save_task(task)
        self.store.save_backlog(self.run_meta.project_name, current_task, tasks, draft=draft)

    def _current_task(self) -> TaskItem:
        return self.store.load_task(self.run_meta.current_task_id)

    def _current_contract(self) -> ContractSpec:
        return self.store.load_contract(self.run_meta.current_task_id)

    def _invoke_phase_adapter(self, adapter: Any, role: str, task: TaskItem, contract: ContractSpec, qa_report: QaReport) -> PhaseEvaluationResult:
        if adapter is None:
            return PhaseEvaluationResult(status="passed", summary="%s not configured" % role)

        if hasattr(adapter, "invoke"):
            result = adapter.invoke(
                role=role,
                workspace=str(self.layout.root),
                task=task.to_dict(),
                contract=contract.to_dict(),
                qa_report=qa_report.to_dict(),
                writable_paths=[str(self.layout.task_reports_dir)],
            )
            payload = result.metadata.get("structured", {}) if isinstance(result, AdapterResult) else {}
            if not payload and isinstance(result, dict):
                payload = result.get("metadata", {}).get("structured", {})
            return coerce_phase_result(payload or {"status": "passed", "summary": "%s completed" % role})

        if hasattr(adapter, "review"):
            review_result = adapter.review(task=task, qa_report=qa_report, contract=contract)
            payload = review_result.metadata.get("structured", {}) if isinstance(review_result, AdapterResult) else {}
            return coerce_phase_result(payload or {"status": "passed", "summary": "%s reviewed" % role})

        return PhaseEvaluationResult(status="passed", summary="%s completed" % role)

    def _handle_intake(self) -> None:
        self.store.write_text(self.layout.runtime / "intake.md", self.run_meta.request_text)
        self._transition(RunState.SPEC_EXPANSION)

    def _handle_spec_expansion(self) -> None:
        approved_spec = None
        try:
            approved_spec = self.store.load_product_spec()
        except ArtifactNotFoundError:
            approved_spec = None
        clarification = analyze_request(
            project=self.run_meta.project_name,
            request_text=self.run_meta.request_text,
            answers=self._load_answers(),
        )
        if not (approved_spec and self._has_approval("spec")):
            self.store.save_product_spec(clarification.spec, draft=True)
        self.store.save_questions(
            {
                "questions": clarification.questions,
                "resolved": clarification.resolved_questions,
                "unresolved": clarification.unresolved_questions,
            }
        )
        self.store.save_decisions({"decisions": clarification.decisions})
        if clarification.unresolved_questions:
            self._block(
                reason="clarification_required",
                resume_from_state=RunState.SPEC_EXPANSION,
                note="waiting for human clarification",
            )
            return

        final_spec = approved_spec if approved_spec and self._has_approval("spec") else clarification.spec
        final_spec.status = "approved" if self._has_approval("spec") else "ready_for_approval"
        final_spec.open_questions = []
        self.store.save_product_spec(final_spec, draft=False)
        if not self._has_approval("spec"):
            self._block(
                reason="spec_approval_required",
                resume_from_state=RunState.BACKLOG_BUILD,
                note="waiting for human spec approval",
            )
            return
        self._transition(RunState.BACKLOG_BUILD)

    def _handle_backlog_build(self) -> None:
        spec = self.store.load_product_spec()
        planning_contract = load_planning_contract(self.layout.root)
        tasks = build_backlog(spec, planning_contract=planning_contract)
        self._persist_tasks(tasks, current_task=None, draft=True)
        if not self._has_approval("backlog"):
            self._block(
                reason="backlog_approval_required",
                resume_from_state=RunState.BACKLOG_BUILD,
                note="waiting for human backlog approval",
            )
            return
        self._persist_tasks(tasks, current_task=None, draft=False)
        self._transition(RunState.TASK_SELECTED)

    def _handle_task_selected(self) -> None:
        tasks = self._load_tasks()
        selected = select_next_task(tasks)
        if selected is None:
            self._transition(RunState.NEXT_TASK)
            return
        selected.status = "in_progress"
        self.run_meta.current_task_id = selected.id
        self.run_meta.repair_count = 0
        self.run_meta.last_failure_signature = None
        self.run_meta.blocked_reason = None
        self.run_meta.resume_from_state = None
        self._persist_tasks(tasks, current_task=selected.id, draft=not self.layout.backlog_path.exists())
        self.store.save_run_state(self.run_meta)
        self._transition(RunState.CONTRACT_NEGOTIATION)

    def _handle_contract_negotiation(self) -> None:
        task = self._current_task()
        planning_contract = load_planning_contract(self.layout.root)
        try:
            contract = build_contract(task, planning_contract=planning_contract if planning_contract and planning_contract.is_ready else None)
            self.contract_gate.validate(task=task, contract=contract)
        except ValueError as exc:
            self._block(
                reason="planning_execution_scope_mismatch",
                resume_from_state=RunState.CONTRACT_NEGOTIATION,
                note=str(exc),
                task_id=task.id,
            )
            return
        self.store.save_contract(contract)
        self._transition(RunState.IMPLEMENTING)

    def _handle_implementing(self) -> None:
        task = self._current_task()
        contract = self._current_contract()
        self._last_implementation = self.codex_writer.execute(
            layout=self.layout,
            task=task,
            contract=contract,
            run_meta=self.run_meta,
        )
        if (
            self._last_implementation.metadata.get("mode") == "hosted_codex"
            and self._last_implementation.metadata.get("status") == "pending_hosted_execution"
        ):
            self.store.write_json(
                self.layout.runtime / "hosted_execution_request.json",
                self._last_implementation.metadata,
            )
            self._block(
                reason="hosted_execution_required",
                resume_from_state=RunState.IMPLEMENTING,
                note="waiting for hosted codex execution result",
                task_id=task.id,
            )
            return
        self.logger.append(self._last_implementation.summary)
        self._transition(RunState.STATIC_REVIEW)

    def _handle_static_review(self) -> None:
        task = self._current_task()
        contract = self._current_contract()
        previous_qa = None
        qa_path = self.layout.task_dir(task.id) / "qa_report.json"
        if qa_path.exists():
            previous_qa = self.store.load_qa_report(task.id)

        backend_review = self.backend_specialist.review(
            layout=self.layout,
            task=task,
            contract=contract,
            qa_report=previous_qa,
        )
        frontend_review = self.frontend_specialist.review(
            layout=self.layout,
            task=task,
            contract=contract,
            qa_report=previous_qa,
        )
        self.store.save_review(task.id, "backend_review.md", backend_review.summary)
        self.store.save_review(task.id, "frontend_review.md", frontend_review.summary)
        self.store.save_proposal(task.id, "backend_patch.diff", backend_review.proposed_patch or "")
        self.store.save_proposal(task.id, "frontend_patch.diff", frontend_review.proposed_patch or "")
        self.store.save_trace(task.id, "backend_specialist.json", backend_review.metadata.get("trace", {}))
        self.store.save_trace(task.id, "frontend_specialist.json", frontend_review.metadata.get("trace", {}))
        self._last_reviews = [backend_review, frontend_review]
        self._last_static = self.static_evaluator.evaluate(task, contract, self._last_implementation, self._last_reviews)
        if self._last_static.status != "passed":
            qa = self.qa_manager.aggregate(
                task=task,
                static_phase=self._last_static,
                runtime_phase=PhaseEvaluationResult(status="skipped", summary="runtime skipped"),
                outcome_phase=PhaseEvaluationResult(status="skipped", summary="outcome skipped"),
            )
            self.store.save_qa_report(task.id, qa)
            self._transition(RunState.REPAIRING)
            return
        self._transition(RunState.RUNTIME_QA)

    def _handle_runtime_qa(self) -> None:
        task = self._current_task()
        contract = self._current_contract()
        runtime_phase = self.runtime_evaluator.evaluate(task, self._last_implementation)
        outcome_phase = self.outcome_evaluator.evaluate(task, self._last_implementation)
        qa = self.qa_manager.aggregate(
            task=task,
            static_phase=self._last_static or PhaseEvaluationResult(status="passed", summary="static review passed"),
            runtime_phase=runtime_phase,
            outcome_phase=outcome_phase,
        )
        backend_eval_adapter = getattr(self.services, "backend_evaluator", None)
        frontend_eval_adapter = getattr(self.services, "frontend_evaluator", None)
        if backend_eval_adapter is not None and frontend_eval_adapter is not None:
            backend_eval = self._invoke_phase_adapter(backend_eval_adapter, "backend_evaluator", task, contract, qa)
            frontend_eval = self._invoke_phase_adapter(frontend_eval_adapter, "frontend_evaluator", task, contract, qa)
            aggregate_phase = self.aggregate_evaluator.merge(backend_eval, frontend_eval)
            combined_findings = self._merge_findings(qa.findings, aggregate_phase.findings)
            review_summary = self._build_review_summary(
                mode="runtime_qa",
                scope="task",
                status="approved" if aggregate_phase.status == "passed" and not combined_findings else "failed",
                summary=aggregate_phase.summary,
                findings=combined_findings,
                failure_signature=qa.failure_signature or aggregate_phase.details.get("failure_signature"),
                next_action="ready_to_commit" if aggregate_phase.status == "passed" and not combined_findings else "repair",
            )
            self._persist_dual_evaluation_artifacts(
                task,
                backend_phase=backend_eval,
                frontend_phase=frontend_eval,
                aggregate_phase=aggregate_phase,
                review_summary=review_summary,
            )
            qa = self.qa_manager.build_report(
                task=task,
                static_status=self._last_static or PhaseEvaluationResult(status="passed", summary="static review passed"),
                runtime_status=runtime_phase,
                outcome_status=aggregate_phase,
                findings=combined_findings,
                failure_signature=qa.failure_signature or aggregate_phase.details.get("failure_signature"),
            )
            qa.backend = aggregate_phase.details.get("backend", {})
            qa.frontend = aggregate_phase.details.get("frontend", {})
            qa.review = review_summary
        self.store.save_qa_report(task.id, qa)
        if qa.status == "approved":
            self._transition(RunState.READY_TO_COMMIT)
            return
        self._transition(RunState.REPAIRING)

    def _handle_repairing(self) -> None:
        task = self._current_task()
        qa_report = self.store.load_qa_report(task.id)
        self.run_meta.repair_count += 1
        decision = repair_decision(
            repair_count=self.run_meta.repair_count,
            repair_budget=task.repair_budget,
            previous_signature=self.run_meta.last_failure_signature or "",
            current_signature=qa_report.failure_signature or "",
        )
        if decision.blocked:
            self._block(
                reason=decision.reason or "repair_blocked",
                resume_from_state=RunState.IMPLEMENTING,
                note="repair loop exhausted or failure signature repeated",
                task_id=task.id,
            )
            return
        self.run_meta.last_failure_signature = qa_report.failure_signature
        self.store.save_repair_notes(task.id, self.services.lead_writer.repair_notes(task, qa_report))
        self.store.save_run_state(self.run_meta)
        self._transition(RunState.IMPLEMENTING)

    def _handle_ready_to_commit(self) -> None:
        task = self._current_task()
        contract = self._current_contract()
        qa_report = self.store.load_qa_report(task.id)
        gate = evaluate_commit_gate(
            workspace=self.layout.root,
            task=task,
            contract=contract,
            qa_report=qa_report,
            implementation=self._last_implementation,
            git_adapter=self.services.git,
        )
        if not gate.passed:
            self._block(
                reason="commit_gate_failed",
                resume_from_state=RunState.READY_TO_COMMIT,
                note="commit gate rejected current task",
                task_id=task.id,
            )
            return
        self.run_meta.commit_log.append(
            {
                "task_id": task.id,
                "message": gate.message,
                "dry_run": gate.dry_run,
                "commit_hash": gate.commit_hash,
            }
        )
        self.store.save_run_state(self.run_meta)
        self._transition(RunState.COMMITTED)

    def _handle_committed(self) -> None:
        tasks = self._load_tasks()
        for task in tasks:
            if task.id == self.run_meta.current_task_id:
                task.status = "done"
                break
        self.run_meta.current_task_id = None
        self._persist_tasks(tasks, current_task=None, draft=not self.layout.backlog_path.exists())
        self.store.save_run_state(self.run_meta)
        self._transition(RunState.NEXT_TASK)

    def _handle_next_task(self) -> None:
        tasks = self._load_tasks()
        selected = select_next_task(tasks)
        self._persist_tasks(tasks, current_task=None, draft=not self.layout.backlog_path.exists())
        if selected is None:
            final_review = self._build_final_review_payload(tasks)
            if final_review["status"] != "approved":
                self._block(
                    reason="final_review_failed",
                    resume_from_state=RunState.NEXT_TASK,
                    note=final_review["summary"],
                    task_id="CHANGE",
                )
                return
            self._transition(RunState.DONE)
            return
        self._transition(RunState.TASK_SELECTED)
