from __future__ import annotations

import json
import os
import shutil
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
        self.router = layout.runtime_router

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

    def _migrate_file(self, source: Path, target: Path) -> None:
        if not source.exists() or target.exists():
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    def _migrate_tree(self, source: Path, target: Path) -> None:
        if not source.exists() or target.exists():
            return
        shutil.copytree(source, target)

    def migrate_legacy_layout(self) -> None:
        self._migrate_file(self.layout.legacy_product_dir / "product_spec.draft.yaml", self.layout.product_spec_draft_path)
        self._migrate_file(self.layout.legacy_product_dir / "product_spec.yaml", self.layout.product_spec_path)
        self._migrate_file(self.layout.legacy_product_dir / "product_spec.md", self.layout.product_spec_markdown_path)
        self._migrate_file(self.layout.legacy_product_dir / "questions.yaml", self.layout.questions_path)
        self._migrate_file(self.layout.legacy_product_dir / "answers.yaml", self.layout.answers_path)
        self._migrate_file(self.layout.legacy_product_dir / "decisions.yaml", self.layout.decisions_path)
        self._migrate_file(self.layout.legacy_planning_dir / "backlog.draft.yaml", self.layout.backlog_draft_path)
        self._migrate_file(self.layout.legacy_planning_dir / "backlog.yaml", self.layout.backlog_path)
        self._migrate_file(self.layout.legacy_planning_dir / "contract.yaml", self.layout.planning_contract_path)
        self._migrate_file(self.layout.legacy_final_review_path, self.layout.final_review_path)
        self._migrate_file(self.layout.legacy_final_review_markdown_path, self.layout.final_review_markdown_path)

    def ensure_runtime_configs(self) -> None:
        self.layout.ensure()
        self.migrate_legacy_layout()
        policies_path = self.layout.policies_path
        models_path = self.layout.models_path
        if not policies_path.exists():
            self.write_yaml(policies_path, default_policies())
        if not models_path.exists():
            self.write_yaml(models_path, default_models())

    def write_run_state(self, meta: RunMeta) -> None:
        self.router.ensure_roots(run_id=meta.run_id)
        self.write_json(self.router.current_run_path, {"run_id": meta.run_id})
        self.write_json(self.router.run_state_path(meta.run_id), meta.to_dict())
        self.write_json(
            self.router.manifest_path(meta.run_id),
            {
                "run_id": meta.run_id,
                "state": meta.state.value,
                "current_task_id": meta.current_task_id,
                "project_name": meta.project_name,
            },
        )

    def write_product_spec(self, spec: ProductSpec, draft: bool = False) -> None:
        yaml_path = self.layout.product_spec_draft_path if draft else self.layout.product_spec_path
        self.write_yaml(yaml_path, spec.to_dict())
        if not draft:
            self.write_text(self.layout.product_spec_markdown_path, render_product_spec_markdown(spec))

    def write_backlog(self, project: str, current_task: Optional[str], items: List[TaskItem], draft: bool = False) -> None:
        path = self.layout.backlog_draft_path if draft else self.layout.backlog_path
        self.write_yaml(path, backlog_payload(project, current_task, items))

    def write_task(self, task: TaskItem) -> None:
        run_id = self.router.require_run_id()
        self.router.ensure_roots(run_id=run_id, task_id=task.id)
        self.write_yaml(self.layout.task_dir(task.id, run_id) / "task.yaml", task.to_dict())

    def write_contract(self, contract: ContractSpec) -> None:
        run_id = self.router.require_run_id()
        self.router.ensure_roots(run_id=run_id, task_id=contract.task_id)
        self.write_yaml(self.layout.task_dir(contract.task_id, run_id) / "contract.yaml", contract.to_dict())
        self.write_text(self.layout.task_dir(contract.task_id, run_id) / "contract.md", render_contract_markdown(contract))

    def write_qa_report(self, task_id: str, qa_report: QaReport) -> None:
        run_id = self.router.require_run_id()
        self.router.ensure_roots(run_id=run_id, task_id=task_id)
        self.write_json(self.layout.task_dir(task_id, run_id) / "qa_report.json", qa_report.to_dict())

    def write_questions(self, payload: Dict[str, Any]) -> None:
        self.layout.ensure()
        self.write_yaml(self.layout.questions_path, payload)

    def write_answers(self, payload: Dict[str, Any]) -> None:
        self.layout.ensure()
        self.write_yaml(self.layout.answers_path, payload)

    def write_decisions(self, payload: Dict[str, Any]) -> None:
        self.layout.ensure()
        self.write_yaml(self.layout.decisions_path, payload)

    def write_approval(self, target: str, approved_by: str, note: str, task_id: str = "") -> Dict[str, Any]:
        payload = {
            "target": target,
            "task_id": task_id or None,
            "approved_by": approved_by,
            "note": note,
        }
        run_id = self.router.require_run_id()
        self.router.ensure_roots(run_id=run_id)
        self.write_json(self.router.approval_path(target, task_id or None, run_id), payload)
        return payload

    def write_repair_notes(self, task_id: str, content: str) -> None:
        run_id = self.router.require_run_id()
        self.router.ensure_roots(run_id=run_id, task_id=task_id)
        self.write_text(self.router.repair_notes_path(task_id, run_id), content)

    def write_review(self, task_id: str, name: str, content: str) -> None:
        run_id = self.router.require_run_id()
        self.router.ensure_roots(run_id=run_id, task_id=task_id)
        self.write_text(self.layout.task_reviews_dir(task_id, run_id) / name, content)

    def write_proposal(self, task_id: str, name: str, content: str) -> None:
        run_id = self.router.require_run_id()
        self.router.ensure_roots(run_id=run_id, task_id=task_id)
        self.write_text(self.layout.task_proposals_dir(task_id, run_id) / name, content)

    def write_trace(self, task_id: str, name: str, payload: Dict[str, Any]) -> None:
        run_id = self.router.require_run_id()
        self.router.ensure_roots(run_id=run_id, task_id=task_id)
        self.write_json(self.layout.task_traces_dir(task_id, run_id) / name, payload)

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
        run_id = self.router.require_run_id()
        self.router.ensure_roots(run_id=run_id)
        self.write_json(self.router.blocked_interrupt_path(run_id), payload)
        return payload

    def write_unblock_decision(self, reason: str, note: str) -> None:
        run_id = self.router.require_run_id()
        self.router.ensure_roots(run_id=run_id)
        self.write_json(self.router.unblock_decision_path(run_id), {"reason": reason, "note": note})

    def clear_blocked_interrupt(self) -> None:
        run_id = self.router.active_run_id()
        if not run_id:
            return
        path = self.router.blocked_interrupt_path(run_id)
        if path.exists():
            path.unlink()

    def record_progress(self, line: str) -> None:
        run_id = self.router.active_run_id()
        progress = self.router.progress_path(run_id) if run_id else self.layout.progress_path
        existing = "# Progress\n\n"
        if progress.exists():
            existing = progress.read_text(encoding="utf-8")
        self.write_text(progress, existing + "- %s\n" % line)
