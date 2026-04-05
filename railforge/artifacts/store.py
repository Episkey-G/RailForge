from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from railforge.artifacts.loaders import ArtifactLoader
from railforge.artifacts.writers import ArtifactWriter
from railforge.core.errors import ArtifactNotFoundError
from railforge.core.models import ContractSpec, ProductSpec, QaReport, RunMeta, TaskItem, WorkspaceLayout


class ArtifactStore:
    def __init__(self, layout: WorkspaceLayout) -> None:
        self.layout = layout
        self.loader = ArtifactLoader(layout)
        self.writer = ArtifactWriter(layout)

    def init_workspace(self) -> None:
        self.layout.ensure()
        self.writer.ensure_runtime_configs()

    def write_text(self, path: Path, content: str) -> None:
        self.writer.write_text(path, content)

    def write_json(self, path: Path, payload: Dict[str, Any]) -> None:
        self.writer.write_json(path, payload)

    def write_yaml(self, path: Path, payload: Dict[str, Any]) -> None:
        self.writer.write_yaml(path, payload)

    def read_text(self, path: Path) -> str:
        return self.loader.read_text(path)

    def read_json(self, path: Path) -> Dict[str, Any]:
        return self.loader.read_json(path)

    def read_yaml(self, path: Path) -> Dict[str, Any]:
        return self.loader.read_yaml(path)

    def save_run_state(self, meta: RunMeta) -> None:
        self.writer.write_run_state(meta)

    def load_run_state(self) -> RunMeta:
        return self.loader.load_run_state()

    def save_product_spec(self, spec: ProductSpec, draft: bool = False) -> None:
        self.writer.write_product_spec(spec, draft=draft)

    def load_product_spec(self, draft: bool = False) -> ProductSpec:
        return self.loader.load_product_spec(draft=draft)

    def save_backlog(self, project: str, current_task: Optional[str], items: List[TaskItem], draft: bool = False) -> None:
        self.writer.write_backlog(project, current_task, items, draft=draft)

    def load_backlog(self, draft: bool = False) -> Dict[str, Any]:
        return self.loader.load_backlog(draft=draft)

    def save_task(self, task: TaskItem) -> None:
        self.writer.write_task(task)

    def load_task(self, task_id: str) -> TaskItem:
        return self.loader.load_task(task_id)

    def save_contract(self, contract: ContractSpec) -> None:
        self.writer.write_contract(contract)

    def load_contract(self, task_id: str) -> ContractSpec:
        return self.loader.load_contract(task_id)

    def save_qa_report(self, task_id: str, qa_report: QaReport) -> None:
        self.writer.write_qa_report(task_id, qa_report)

    def load_qa_report(self, task_id: str) -> QaReport:
        return self.loader.load_qa_report(task_id)

    def save_repair_notes(self, task_id: str, content: str) -> None:
        self.writer.write_repair_notes(task_id, content)

    def save_review(self, task_id: str, name: str, content: str) -> None:
        self.writer.write_review(task_id, name, content)

    def save_proposal(self, task_id: str, name: str, content: str) -> None:
        self.writer.write_proposal(task_id, name, content)

    def save_trace(self, task_id: str, name: str, payload: Dict[str, Any]) -> None:
        self.writer.write_trace(task_id, name, payload)

    def save_unblock_decision(self, reason: str, note: str) -> None:
        self.writer.write_unblock_decision(reason, note)

    def load_unblock_decision(self) -> Dict[str, Any]:
        return self.loader.load_unblock_decision()

    def save_questions(self, payload: Dict[str, Any]) -> None:
        self.writer.write_questions(payload)

    def load_questions(self) -> Dict[str, Any]:
        return self.loader.load_questions()

    def save_answers(self, payload: Dict[str, Any]) -> None:
        self.writer.write_answers(payload)

    def load_answers(self) -> Dict[str, Any]:
        return self.loader.load_answers()

    def save_decisions(self, payload: Dict[str, Any]) -> None:
        self.writer.write_decisions(payload)

    def load_decisions(self) -> Dict[str, Any]:
        return self.loader.load_decisions()

    def save_approval(self, target: str, approved_by: str, note: str, task_id: str = "") -> Dict[str, Any]:
        return self.writer.write_approval(target=target, approved_by=approved_by, note=note, task_id=task_id)

    def load_approval(self, target: str, task_id: str = "") -> Dict[str, Any]:
        return self.loader.load_approval(target=target, task_id=task_id)

    def has_approval(self, target: str, task_id: str = "") -> bool:
        try:
            self.load_approval(target=target, task_id=task_id)
        except ArtifactNotFoundError:
            return False
        return True

    def save_blocked_interrupt(
        self,
        task_id: str,
        reason: str,
        resume_from_state: str,
        note: str,
    ) -> Dict[str, Any]:
        return self.writer.write_blocked_interrupt(task_id, reason, resume_from_state, note)

    def load_blocked_interrupt(self) -> Dict[str, Any]:
        return self.loader.load_blocked_interrupt()

    def clear_blocked_interrupt(self) -> None:
        self.writer.clear_blocked_interrupt()

    def record_progress(self, line: str) -> None:
        self.writer.record_progress(line)
