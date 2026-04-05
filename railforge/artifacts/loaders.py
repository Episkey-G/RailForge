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
        self.router = layout.runtime_router

    @staticmethod
    def _first_existing(*paths: Path) -> Path:
        for path in paths:
            if path.exists():
                return path
        return paths[0]

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
        run_id = self.router.active_run_id()
        if run_id:
            return RunMeta.from_dict(self.read_json(self.router.run_state_path(run_id)))
        return RunMeta.from_dict(self.read_json(self.router.legacy_run_state_path))

    def load_product_spec(self, draft: bool = False) -> ProductSpec:
        path = self._first_existing(
            self.layout.product_spec_draft_path if draft else self.layout.product_spec_path,
            self.layout.legacy_product_dir / ("product_spec.draft.yaml" if draft else "product_spec.yaml"),
        )
        return ProductSpec.from_dict(self.read_yaml(path))

    def load_backlog(self, draft: bool = False) -> Dict[str, Any]:
        path = self._first_existing(
            self.layout.backlog_draft_path if draft else self.layout.backlog_path,
            self.layout.legacy_planning_dir / ("backlog.draft.yaml" if draft else "backlog.yaml"),
        )
        return self.read_yaml(path)

    def load_task(self, task_id: str) -> TaskItem:
        active_run = self.router.active_run_id()
        path = self._first_existing(
            self.layout.task_dir(task_id, active_run) / "task.yaml" if active_run else self.layout.runtime / "__missing__",
            self.layout.legacy_execution_dir / "tasks" / task_id / "task.yaml",
        )
        return TaskItem.from_dict(self.read_yaml(path))

    def load_contract(self, task_id: str) -> ContractSpec:
        active_run = self.router.active_run_id()
        path = self._first_existing(
            self.layout.task_dir(task_id, active_run) / "contract.yaml" if active_run else self.layout.runtime / "__missing__",
            self.layout.legacy_execution_dir / "tasks" / task_id / "contract.yaml",
        )
        return ContractSpec.from_dict(self.read_yaml(path))

    def load_qa_report(self, task_id: str) -> QaReport:
        active_run = self.router.active_run_id()
        path = self._first_existing(
            self.layout.task_dir(task_id, active_run) / "qa_report.json" if active_run else self.layout.runtime / "__missing__",
            self.layout.legacy_execution_dir / "tasks" / task_id / "qa_report.json",
        )
        return QaReport.from_dict(self.read_json(path))

    def load_questions(self) -> Dict[str, Any]:
        path = self._first_existing(self.layout.questions_path, self.layout.legacy_product_dir / "questions.yaml")
        return self.read_yaml(path)

    def load_answers(self) -> Dict[str, Any]:
        path = self._first_existing(self.layout.answers_path, self.layout.legacy_product_dir / "answers.yaml")
        return self.read_yaml(path)

    def load_decisions(self) -> Dict[str, Any]:
        path = self._first_existing(self.layout.decisions_path, self.layout.legacy_product_dir / "decisions.yaml")
        return self.read_yaml(path)

    def load_approval(self, target: str, task_id: str = "") -> Dict[str, Any]:
        active_run = self.router.active_run_id()
        path = self._first_existing(
            self.router.approval_path(target, task_id or None, active_run) if active_run else self.layout.runtime / "__missing__",
            self.layout.runtime / "approvals" / ("%s.json" % (target if not task_id else "%s-%s" % (target, task_id))),
        )
        return self.read_json(path)

    def load_unblock_decision(self) -> Dict[str, Any]:
        active_run = self.router.active_run_id()
        path = self._first_existing(
            self.router.unblock_decision_path(active_run) if active_run else self.layout.runtime / "__missing__",
            self.layout.runtime / "interrupts" / "unblock_decision.json",
        )
        return self.read_json(path)

    def load_blocked_interrupt(self) -> Dict[str, Any]:
        active_run = self.router.active_run_id()
        path = self._first_existing(
            self.router.blocked_interrupt_path(active_run) if active_run else self.layout.runtime / "__missing__",
            self.layout.runtime / "interrupts" / "blocked_interrupt.json",
        )
        return self.read_json(path)
