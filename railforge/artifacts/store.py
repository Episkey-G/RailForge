from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from railforge.artifacts.loaders import ArtifactLoader
from railforge.artifacts.writers import ArtifactWriter
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

    def save_product_spec(self, spec: ProductSpec) -> None:
        self.writer.write_product_spec(spec)

    def load_product_spec(self) -> ProductSpec:
        return self.loader.load_product_spec()

    def save_backlog(self, project: str, current_task: Optional[str], items: List[TaskItem]) -> None:
        self.writer.write_backlog(project, current_task, items)

    def load_backlog(self) -> Dict[str, Any]:
        return self.loader.load_backlog()

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

    def save_unblock_decision(self, reason: str, note: str) -> None:
        self.writer.write_unblock_decision(reason, note)

    def load_unblock_decision(self) -> Dict[str, Any]:
        return self.loader.load_unblock_decision()

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

    def record_progress(self, line: str) -> None:
        self.writer.record_progress(line)
