from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


class RuntimeArtifactRouter:
    def __init__(self, layout) -> None:
        self.layout = layout

    @property
    def current_run_path(self) -> Path:
        return self.layout.runtime / "current_run.json"

    @property
    def runs_dir(self) -> Path:
        return self.layout.runtime / "runs"

    @property
    def checkpoints_dir(self) -> Path:
        return self.layout.runtime / "checkpoints"

    @property
    def approvals_dir(self) -> Path:
        return self.layout.runtime / "approvals"

    @property
    def execution_requests_dir(self) -> Path:
        return self.layout.runtime / "execution_requests"

    @property
    def execution_results_dir(self) -> Path:
        return self.layout.runtime / "execution_results"

    @property
    def traces_dir(self) -> Path:
        return self.layout.runtime / "traces"

    @property
    def reviews_dir(self) -> Path:
        return self.layout.runtime / "reviews"

    @property
    def proposals_dir(self) -> Path:
        return self.layout.runtime / "proposals"

    @property
    def failure_signatures_dir(self) -> Path:
        return self.layout.runtime / "failure_signatures"

    @property
    def notes_dir(self) -> Path:
        return self.layout.runtime / "notes"

    @property
    def legacy_run_state_path(self) -> Path:
        return self.layout.runtime / "run_state.json"

    @property
    def legacy_hosted_execution_request_path(self) -> Path:
        return self.layout.runtime / "hosted_execution_request.json"

    @property
    def legacy_hosted_execution_result_path(self) -> Path:
        return self.layout.runtime / "hosted_execution_result.json"

    def active_run_id(self) -> Optional[str]:
        if self.current_run_path.exists():
            payload = json.loads(self.current_run_path.read_text(encoding="utf-8"))
            run_id = str(payload.get("run_id") or "").strip()
            if run_id:
                return run_id
        if self.legacy_run_state_path.exists():
            payload = json.loads(self.legacy_run_state_path.read_text(encoding="utf-8"))
            run_id = str(payload.get("run_id") or "").strip()
            if run_id:
                return run_id
        return None

    def require_run_id(self, run_id: Optional[str] = None) -> str:
        resolved = run_id or self.active_run_id()
        if not resolved:
            raise ValueError("runtime artifact path requires an active run_id")
        return resolved

    def run_dir(self, run_id: Optional[str] = None) -> Path:
        return self.runs_dir / self.require_run_id(run_id)

    def run_state_path(self, run_id: Optional[str] = None) -> Path:
        return self.run_dir(run_id) / "run_state.json"

    def manifest_path(self, run_id: Optional[str] = None) -> Path:
        return self.run_dir(run_id) / "manifest.json"

    def progress_path(self, run_id: Optional[str] = None) -> Path:
        return self.run_dir(run_id) / "progress.md"

    def tasks_dir(self, run_id: Optional[str] = None) -> Path:
        return self.run_dir(run_id) / "tasks"

    def task_dir(self, task_id: str, run_id: Optional[str] = None) -> Path:
        return self.tasks_dir(run_id) / task_id

    def checkpoint_dir(self, run_id: Optional[str] = None) -> Path:
        return self.checkpoints_dir / self.require_run_id(run_id)

    def approval_dir(self, run_id: Optional[str] = None) -> Path:
        return self.approvals_dir / self.require_run_id(run_id)

    def approval_path(self, target: str, task_id: Optional[str] = None, run_id: Optional[str] = None) -> Path:
        name = target if not task_id else "%s-%s" % (target, task_id)
        return self.approval_dir(run_id) / ("%s.json" % name)

    def execution_request_path(self, task_id: str, run_id: Optional[str] = None, kind: str = "hosted_codex") -> Path:
        return self.execution_requests_dir / self.require_run_id(run_id) / task_id / ("%s.json" % kind)

    def execution_result_path(self, task_id: str, run_id: Optional[str] = None, kind: str = "hosted_codex") -> Path:
        return self.execution_results_dir / self.require_run_id(run_id) / task_id / ("%s.json" % kind)

    def trace_dir(self, task_id: str, run_id: Optional[str] = None) -> Path:
        return self.traces_dir / self.require_run_id(run_id) / task_id

    def review_dir(self, task_id: str, run_id: Optional[str] = None) -> Path:
        return self.reviews_dir / self.require_run_id(run_id) / task_id

    def proposal_dir(self, task_id: str, run_id: Optional[str] = None) -> Path:
        return self.proposals_dir / self.require_run_id(run_id) / task_id

    def note_dir(self, task_id: str, run_id: Optional[str] = None) -> Path:
        return self.notes_dir / self.require_run_id(run_id) / task_id

    def run_note_path(self, name: str, run_id: Optional[str] = None) -> Path:
        return self.notes_dir / self.require_run_id(run_id) / name

    def repair_notes_path(self, task_id: str, run_id: Optional[str] = None) -> Path:
        return self.note_dir(task_id, run_id) / "repair_notes.md"

    def blocked_interrupt_path(self, run_id: Optional[str] = None) -> Path:
        return self.notes_dir / self.require_run_id(run_id) / "interrupts" / "blocked_interrupt.json"

    def unblock_decision_path(self, run_id: Optional[str] = None) -> Path:
        return self.notes_dir / self.require_run_id(run_id) / "interrupts" / "unblock_decision.json"

    def failure_signature_path(self, task_id: str, run_id: Optional[str] = None) -> Path:
        return self.failure_signatures_dir / self.require_run_id(run_id) / ("%s.json" % task_id)

    def ensure_roots(self, run_id: Optional[str] = None, task_id: Optional[str] = None) -> None:
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.approvals_dir.mkdir(parents=True, exist_ok=True)
        self.execution_requests_dir.mkdir(parents=True, exist_ok=True)
        self.execution_results_dir.mkdir(parents=True, exist_ok=True)
        self.traces_dir.mkdir(parents=True, exist_ok=True)
        self.reviews_dir.mkdir(parents=True, exist_ok=True)
        self.proposals_dir.mkdir(parents=True, exist_ok=True)
        self.failure_signatures_dir.mkdir(parents=True, exist_ok=True)
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        if run_id:
            self.run_dir(run_id).mkdir(parents=True, exist_ok=True)
            self.tasks_dir(run_id).mkdir(parents=True, exist_ok=True)
            self.checkpoint_dir(run_id).mkdir(parents=True, exist_ok=True)
            self.approval_dir(run_id).mkdir(parents=True, exist_ok=True)
            (self.notes_dir / run_id / "interrupts").mkdir(parents=True, exist_ok=True)
        if run_id and task_id:
            self.task_dir(task_id, run_id).mkdir(parents=True, exist_ok=True)
            self.trace_dir(task_id, run_id).mkdir(parents=True, exist_ok=True)
            self.review_dir(task_id, run_id).mkdir(parents=True, exist_ok=True)
            self.proposal_dir(task_id, run_id).mkdir(parents=True, exist_ok=True)
            self.note_dir(task_id, run_id).mkdir(parents=True, exist_ok=True)
            self.execution_request_path(task_id, run_id).parent.mkdir(parents=True, exist_ok=True)
            self.execution_result_path(task_id, run_id).parent.mkdir(parents=True, exist_ok=True)
            self.failure_signature_path(task_id, run_id).parent.mkdir(parents=True, exist_ok=True)
