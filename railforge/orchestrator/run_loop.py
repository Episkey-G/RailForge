from __future__ import annotations

from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from railforge.adapters.base import HarnessServices
from railforge.artifacts.store import ArtifactStore
from railforge.core.enums import RunState
from railforge.core.errors import ResumeError
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
from railforge.evaluator.outcome_eval import OutcomeEvaluator
from railforge.evaluator.qa_manager import QaManager
from railforge.evaluator.runtime_eval import RuntimeEvaluator
from railforge.evaluator.static_eval import StaticEvaluator
from railforge.execution.backend_specialist import BackendSpecialistService
from railforge.execution.codex_writer import CodexWriterService
from railforge.execution.frontend_specialist import FrontendSpecialistService
from railforge.guardrails.budgets import repair_decision
from railforge.infra.file_lock import WorkspaceLock
from railforge.planner.backlog_builder import build_backlog
from railforge.planner.contract_builder import build_contract
from railforge.planner.spec_expander import expand_request
from railforge.planner.task_selector import select_next_task
from railforge.infra.checkpoint_store import FileCheckpointStore
from railforge.infra.run_logger import RunLogger
from .contract_gate import ContractGate
from .commit_gate import evaluate_commit_gate
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
        self.static_evaluator = StaticEvaluator()
        self.runtime_evaluator = RuntimeEvaluator()
        self.outcome_evaluator = OutcomeEvaluator()
        self.qa_manager = QaManager()
        self.codex_writer = CodexWriterService(self.services.lead_writer)
        self.backend_specialist = BackendSpecialistService(self.services.backend_specialist)
        self.frontend_specialist = FrontendSpecialistService(self.services.frontend_specialist)
        self.run_meta = None  # type: Optional[RunMeta]
        self._last_implementation = None  # type: Optional[AdapterResult]
        self._last_static = None  # type: Optional[PhaseEvaluationResult]
        self._last_reviews = []  # type: List[AdapterResult]

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
            self.run_meta = self.store.load_run_state()
            if self.run_meta.state != RunState.BLOCKED:
                raise ResumeError("run is not blocked")
            if not self.run_meta.resume_from_state:
                raise ResumeError("blocked run has no resume_from_state")
            self.interrupts.record_unblock(reason=reason, note=note)
            self.run_meta.state = RunState(self.run_meta.resume_from_state)
            self.run_meta.blocked_reason = None
            self.run_meta.repair_count = 0
            self.run_meta.last_failure_signature = None
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
        self.store.save_run_state(self.run_meta)
        self.logger.append("STATE -> %s" % nxt.value)
        self._snapshot()

    def _snapshot(self) -> None:
        current_task = None
        backlog = {"items": []}
        if (self.layout.rf / "backlog.yaml").exists():
            backlog = self.store.load_backlog()
        if self.run_meta and self.run_meta.current_task_id:
            task_path = self.layout.task_dir(self.run_meta.current_task_id) / "task.yaml"
            if task_path.exists():
                current_task = self.store.load_task(self.run_meta.current_task_id)
        checkpoint = self.checkpoints.save(self.run_meta, backlog, current_task)
        self.run_meta.checkpoint_index = checkpoint.sequence
        self.store.save_run_state(self.run_meta)

    def _load_tasks(self) -> List[TaskItem]:
        backlog = self.store.load_backlog()
        return [TaskItem.from_dict(item) for item in backlog.get("items", [])]

    def _persist_tasks(self, tasks: List[TaskItem], current_task: Optional[str]) -> None:
        for task in tasks:
            self.store.save_task(task)
        self.store.save_backlog(self.run_meta.project_name, current_task, tasks)

    def _current_task(self) -> TaskItem:
        return self.store.load_task(self.run_meta.current_task_id)

    def _current_contract(self) -> ContractSpec:
        return self.store.load_contract(self.run_meta.current_task_id)

    def _handle_intake(self) -> None:
        self.store.write_text(self.layout.rf / "intake.md", self.run_meta.request_text)
        self._transition(RunState.SPEC_EXPANSION)

    def _handle_spec_expansion(self) -> None:
        spec = expand_request(project=self.run_meta.project_name, request_text=self.run_meta.request_text)
        self.store.save_product_spec(spec)
        self._transition(RunState.BACKLOG_BUILD)

    def _handle_backlog_build(self) -> None:
        spec = self.store.load_product_spec()
        tasks = build_backlog(spec)
        self._persist_tasks(tasks, current_task=None)
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
        self._persist_tasks(tasks, current_task=selected.id)
        self.store.save_run_state(self.run_meta)
        self._transition(RunState.CONTRACT_NEGOTIATION)

    def _handle_contract_negotiation(self) -> None:
        task = self._current_task()
        contract = build_contract(task)
        self.contract_gate.validate(task=task, contract=contract)
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
        runtime_phase = self.runtime_evaluator.evaluate(task, self._last_implementation)
        outcome_phase = self.outcome_evaluator.evaluate(task, self._last_implementation)
        qa = self.qa_manager.aggregate(
            task=task,
            static_phase=self._last_static or PhaseEvaluationResult(status="passed", summary="static review passed"),
            runtime_phase=runtime_phase,
            outcome_phase=outcome_phase,
        )
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
            self.run_meta.blocked_reason = decision.reason
            self.run_meta.resume_from_state = RunState.IMPLEMENTING.value
            self.interrupts.record_blocked(
                task_id=task.id,
                reason=decision.reason or "repair_blocked",
                resume_from_state=self.run_meta.resume_from_state,
                note="repair loop exhausted or failure signature repeated",
            )
            self.store.save_run_state(self.run_meta)
            self._transition(RunState.BLOCKED)
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
            self.run_meta.blocked_reason = "commit_gate_failed"
            self.run_meta.resume_from_state = RunState.READY_TO_COMMIT.value
            self.interrupts.record_blocked(
                task_id=task.id,
                reason="commit_gate_failed",
                resume_from_state=self.run_meta.resume_from_state,
                note="commit gate rejected current task",
            )
            self.store.save_run_state(self.run_meta)
            self._transition(RunState.BLOCKED)
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
        self._persist_tasks(tasks, current_task=None)
        self.store.save_run_state(self.run_meta)
        self._transition(RunState.NEXT_TASK)

    def _handle_next_task(self) -> None:
        tasks = self._load_tasks()
        selected = select_next_task(tasks)
        self._persist_tasks(tasks, current_task=None)
        if selected is None:
            self._transition(RunState.DONE)
            return
        self._transition(RunState.TASK_SELECTED)
