from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from railforge.core.models import ContractSpec, ProductSpec, QaReport, RunMeta, TaskItem, WorkspaceLayout
from railforge.core.schemas import (
    backlog_payload,
    default_models,
    default_policies,
    render_contract_markdown,
    render_product_spec_markdown,
)


class ArtifactWriter:
    def __init__(self, layout: WorkspaceLayout) -> None:
        self.layout = layout

    def _atomic_write(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), prefix=path.name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(content)
            os.replace(tmp_path, path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def write_text(self, path: Path, content: str) -> None:
        self._atomic_write(path, content)

    def write_json(self, path: Path, payload: Dict[str, Any]) -> None:
        self._atomic_write(path, json.dumps(payload, indent=2, ensure_ascii=False))

    def write_yaml(self, path: Path, payload: Dict[str, Any]) -> None:
        self._atomic_write(path, yaml.safe_dump(payload, allow_unicode=True, sort_keys=False))

    def ensure_runtime_configs(self) -> None:
        self.layout.ensure()
        policies_path = self.layout.rf / "policies.yaml"
        models_path = self.layout.rf / "models.yaml"
        if not policies_path.exists():
            self.write_yaml(policies_path, default_policies())
        if not models_path.exists():
            self.write_yaml(models_path, default_models())

    def write_run_state(self, meta: RunMeta) -> None:
        self.write_json(self.layout.rf / "run_state.json", meta.to_dict())

    def write_product_spec(self, spec: ProductSpec) -> None:
        self.write_yaml(self.layout.rf / "product_spec.yaml", spec.to_dict())
        self.write_text(self.layout.rf / "product_spec.md", render_product_spec_markdown(spec))

    def write_backlog(self, project: str, current_task: Optional[str], items: List[TaskItem]) -> None:
        self.write_yaml(self.layout.rf / "backlog.yaml", backlog_payload(project, current_task, items))

    def write_task(self, task: TaskItem) -> None:
        self.layout.ensure(task.id)
        self.write_yaml(self.layout.task_dir(task.id) / "task.yaml", task.to_dict())

    def write_contract(self, contract: ContractSpec) -> None:
        self.layout.ensure(contract.task_id)
        self.write_yaml(self.layout.task_dir(contract.task_id) / "contract.yaml", contract.to_dict())
        self.write_text(self.layout.task_dir(contract.task_id) / "contract.md", render_contract_markdown(contract))

    def write_qa_report(self, task_id: str, qa_report: QaReport) -> None:
        self.layout.ensure(task_id)
        self.write_json(self.layout.task_dir(task_id) / "qa_report.json", qa_report.to_dict())

    def write_repair_notes(self, task_id: str, content: str) -> None:
        self.layout.ensure(task_id)
        self.write_text(self.layout.task_dir(task_id) / "repair_notes.md", content)

    def write_review(self, task_id: str, name: str, content: str) -> None:
        self.layout.ensure(task_id)
        self.write_text(self.layout.task_reviews_dir(task_id) / name, content)

    def write_proposal(self, task_id: str, name: str, content: str) -> None:
        self.layout.ensure(task_id)
        self.write_text(self.layout.task_proposals_dir(task_id) / name, content)

    def write_blocked_interrupt(
        self,
        task_id: str,
        reason: str,
        resume_from_state: str,
        note: str,
    ) -> Dict[str, Any]:
        payload = {
            "task_id": task_id,
            "reason": reason,
            "resume_from_state": resume_from_state,
            "note": note,
        }
        self.write_json(self.layout.rf / "blocked_interrupt.json", payload)
        return payload

    def write_unblock_decision(self, reason: str, note: str) -> None:
        self.write_json(self.layout.rf / "unblock_decision.json", {"reason": reason, "note": note})

    def record_progress(self, line: str) -> None:
        progress = self.layout.rf / "progress.md"
        existing = "# Progress\n\n"
        if progress.exists():
            existing = progress.read_text(encoding="utf-8")
        self.write_text(progress, existing + "- %s\n" % line)
