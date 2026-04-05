from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from railforge.artifacts.store import ArtifactStore
from railforge.core.errors import ArtifactNotFoundError
from railforge.core.models import RunMeta, WorkspaceLayout
from railforge.planner.planning_contract import load_planning_contract_truth, planning_contract_gate_state
from railforge.workflow.assets import WorkflowAssetResolver


class ContextAssembler:
    def __init__(
        self,
        layout: WorkspaceLayout,
        store: ArtifactStore,
        asset_resolver: Optional[WorkflowAssetResolver] = None,
    ) -> None:
        self.layout = layout
        self.store = store
        self.asset_resolver = asset_resolver or WorkflowAssetResolver()

    def build(
        self,
        *,
        phase: str,
        run_meta: Optional[RunMeta] = None,
        task_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        effective_run_meta = run_meta or self._load_run_meta()
        effective_task_id = task_id or (effective_run_meta.current_task_id if effective_run_meta else None)
        active_run_id = self.layout.runtime_router.active_run_id()
        approvals = self._approvals()
        planning_truth = load_planning_contract_truth(self.layout.root)
        contract_gate = planning_contract_gate_state(
            self.layout.root,
            backlog_approved=bool(approvals.get("backlog")),
            contract_approved=bool(approvals.get("contract")),
        )
        payload = {
            "phase": phase,
            "workspace": str(self.layout.root),
            "paths": {
                "docs": str(self.layout.docs.relative_to(self.layout.root)),
                "openspec": "openspec",
                "product": str(self.layout.product_dir.relative_to(self.layout.root)),
                "planning": str(self.layout.planning_dir.relative_to(self.layout.root)),
                "planning_contract_truth": str(self.layout.planning_contract_path.relative_to(self.layout.root)),
                "quality": str(self.layout.quality_dir.relative_to(self.layout.root)),
                "runtime": str(self.layout.runtime.relative_to(self.layout.root)),
                "runtime_runs": str(self.layout.runtime_router.runs_dir.relative_to(self.layout.root)),
            },
            "sources": {
                "docs_truth": [
                    str(self.layout.product_spec_path.relative_to(self.layout.root)),
                    str(self.layout.backlog_path.relative_to(self.layout.root)),
                    str(self.layout.planning_contract_path.relative_to(self.layout.root)),
                    str(self.layout.final_review_path.relative_to(self.layout.root)),
                ],
                "runtime_approvals": str(self.layout.runtime_router.approvals_dir.relative_to(self.layout.root)),
                "recent_execution": [
                    str(self._current_execution_request_path(effective_task_id).relative_to(self.layout.root)),
                    str(self._current_execution_result_path(effective_task_id).relative_to(self.layout.root)),
                    str(self._blocked_interrupt_path(active_run_id).relative_to(self.layout.root)),
                ],
            },
            "phase_contract": self.asset_resolver.load_phase_contract(phase),
            "references": self.asset_resolver.load_phase_references(phase),
            "approvals": approvals,
            "product_spec": self._load_optional_yaml_path(self.layout.product_spec_path, self.layout.product_spec_draft_path),
            "questions": self._load_optional_dict("questions"),
            "decisions": self._load_optional_dict("decisions"),
            "backlog": self._load_optional_yaml_path(self.layout.backlog_path, self.layout.backlog_draft_path),
            "planning_contract": planning_truth.payload,
            "contract_gate": contract_gate,
            "run_state": effective_run_meta.to_dict() if effective_run_meta else {},
            "recent_execution": {
                "current_task_id": effective_task_id,
                "hosted_request": self._load_optional_json(self._current_execution_request_path(effective_task_id)),
                "hosted_result": self._load_optional_json(self._current_execution_result_path(effective_task_id)),
                "blocked_interrupt": self._load_optional_json(self._blocked_interrupt_path(active_run_id)),
            },
            "task": self._task_payload(effective_task_id),
            "review": self._review_payload(effective_task_id),
            "extra": dict(extra or {}),
        }
        self.store.write_json(self.layout.context_pack_path(phase), payload)
        return payload

    def _load_run_meta(self) -> Optional[RunMeta]:
        try:
            return self.store.load_run_state()
        except ArtifactNotFoundError:
            return None

    def _load_optional_dict(self, kind: str) -> Dict[str, Any]:
        try:
            if kind == "questions":
                return self.store.load_questions()
            if kind == "decisions":
                return self.store.load_decisions()
        except ArtifactNotFoundError:
            return {}
        return {}

    def _load_optional_json(self, path: Path) -> Dict[str, Any]:
        try:
            return self.store.read_json(path)
        except ArtifactNotFoundError:
            return {}

    def _load_optional_yaml_path(self, *paths: Path) -> Dict[str, Any]:
        for path in paths:
            try:
                return self.store.read_yaml(path)
            except ArtifactNotFoundError:
                continue
        return {}

    def _approvals(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        active_run_id = self.layout.runtime_router.active_run_id()
        if not active_run_id:
            return payload
        approval_dir = self.layout.runtime_router.approval_dir(active_run_id)
        for path in sorted(approval_dir.glob("*.json")):
            payload[path.stem] = self._load_optional_json(path)
        return payload

    def _task_payload(self, task_id: Optional[str]) -> Dict[str, Any]:
        if not task_id:
            return {}
        payload = {
            "task_id": task_id,
            "task": self._load_optional_yaml_path(self.layout.task_dir(task_id) / "task.yaml"),
            "contract": self._load_optional_yaml_path(self.layout.task_dir(task_id) / "contract.yaml"),
            "allowed_paths": [],
        }
        if payload["contract"]:
            payload["allowed_paths"] = list(payload["contract"].get("allowed_paths", []))
        return payload

    def _review_payload(self, task_id: Optional[str]) -> Dict[str, Any]:
        payload = {
            "qa_report": {},
            "final_review": self._load_optional_json(self.layout.final_review_path),
            "rubric": self.asset_resolver.load_review_rubric(),
        }
        if not task_id:
            return payload
        payload["qa_report"] = self._load_optional_json(self.layout.task_dir(task_id) / "qa_report.json")
        return payload

    def _current_execution_request_path(self, task_id: Optional[str]) -> Path:
        if not task_id:
            return self.layout.runtime_router.legacy_hosted_execution_request_path
        return self.layout.runtime_router.execution_request_path(task_id)

    def _current_execution_result_path(self, task_id: Optional[str]) -> Path:
        if not task_id:
            return self.layout.runtime_router.legacy_hosted_execution_result_path
        return self.layout.runtime_router.execution_result_path(task_id)

    def _blocked_interrupt_path(self, run_id: Optional[str]) -> Path:
        if not run_id:
            return self.layout.runtime / "interrupts" / "blocked_interrupt.json"
        return self.layout.runtime_router.blocked_interrupt_path(run_id)
