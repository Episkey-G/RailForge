from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import yaml

from railforge.core.errors import ArtifactNotFoundError
from railforge.core.models import ContractSpec, ProductSpec, QaReport, RunMeta, TaskItem, WorkspaceLayout


class ArtifactLoader:
    def __init__(self, layout: WorkspaceLayout) -> None:
        self.layout = layout

    def read_text(self, path: Path) -> str:
        if not path.exists():
            raise ArtifactNotFoundError(str(path))
        return path.read_text(encoding="utf-8")

    def read_json(self, path: Path) -> Dict[str, Any]:
        return json.loads(self.read_text(path))

    def read_yaml(self, path: Path) -> Dict[str, Any]:
        payload = yaml.safe_load(self.read_text(path))
        return payload or {}

    def load_run_state(self) -> RunMeta:
        return RunMeta.from_dict(self.read_json(self.layout.rf / "run_state.json"))

    def load_product_spec(self) -> ProductSpec:
        return ProductSpec.from_dict(self.read_yaml(self.layout.rf / "product_spec.yaml"))

    def load_backlog(self) -> Dict[str, Any]:
        return self.read_yaml(self.layout.rf / "backlog.yaml")

    def load_task(self, task_id: str) -> TaskItem:
        return TaskItem.from_dict(self.read_yaml(self.layout.task_dir(task_id) / "task.yaml"))

    def load_contract(self, task_id: str) -> ContractSpec:
        return ContractSpec.from_dict(self.read_yaml(self.layout.task_dir(task_id) / "contract.yaml"))

    def load_qa_report(self, task_id: str) -> QaReport:
        return QaReport.from_dict(self.read_json(self.layout.task_dir(task_id) / "qa_report.json"))

    def load_unblock_decision(self) -> Dict[str, Any]:
        return self.read_json(self.layout.rf / "unblock_decision.json")

    def load_blocked_interrupt(self) -> Dict[str, Any]:
        return self.read_json(self.layout.rf / "blocked_interrupt.json")
