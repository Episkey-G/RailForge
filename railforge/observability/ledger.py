from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from railforge.artifacts.store import ArtifactStore
from railforge.core.models import QaReport, WorkspaceLayout


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class FailureAttribution:
    category: str
    reason: str
    signature: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "reason": self.reason,
            "signature": self.signature,
        }


def classify_failure(reason: str, signature: Optional[str] = None) -> FailureAttribution:
    if reason in {"clarification_required", "spec_approval_required", "backlog_approval_required", "contract_approval_required"}:
        category = "spec_defect"
    elif reason in {"review_context_missing", "qa_report_missing"}:
        category = "workflow_skill_defect"
    elif reason in {"run_state_missing", "blocked_without_resume", "current_task_missing", "recovery_failed"}:
        category = "context_assembly_defect"
    elif reason in {"hosted_execution_required", "provider_fault", "tool_fault"}:
        category = "provider_tool_fault"
    else:
        category = "deterministic_gate_gap"
    return FailureAttribution(category=category, reason=reason, signature=signature)


class ObservabilityLedger:
    def __init__(self, layout: WorkspaceLayout, store: ArtifactStore) -> None:
        self.layout = layout
        self.store = store

    @property
    def run_ledger_path(self) -> Path:
        run_id = self.layout.runtime_router.active_run_id() or "unbound"
        return self.layout.ledgers_dir / f"{run_id}.jsonl"

    @property
    def latest_verdict_path(self) -> Path:
        run_id = self.layout.runtime_router.active_run_id() or "unbound"
        return self.layout.ledgers_dir / f"{run_id}.latest_verdict.json"

    @staticmethod
    def quality_grade(status: str, finding_count: int) -> str:
        if status == "approved" and finding_count == 0:
            return "A"
        if status == "approved":
            return "B"
        if finding_count <= 1:
            return "C"
        return "D"

    def append(self, event_type: str, payload: Dict[str, Any]) -> None:
        self.layout.ensure()
        line = json.dumps(
            {
                "ts": _utc_now(),
                "event": event_type,
                "payload": payload,
            },
            ensure_ascii=False,
        )
        existing = ""
        if self.run_ledger_path.exists():
            existing = self.run_ledger_path.read_text(encoding="utf-8")
        self.store.write_text(self.run_ledger_path, existing + line + "\n")

    def record_state_transition(self, *, previous: str, current: str, task_id: Optional[str]) -> None:
        self.append(
            "state_transition",
            {
                "previous": previous,
                "current": current,
                "task_id": task_id,
            },
        )

    def record_tool_invocation(self, *, role: str, payload: Dict[str, Any]) -> None:
        self.append("tool_invocation", {"role": role, **payload})

    def record_review_findings(self, *, task_id: str, findings: list[dict[str, Any]], verdict: str) -> None:
        self.append(
            "review_findings",
            {
                "task_id": task_id,
                "verdict": verdict,
                "findings": findings,
            },
        )

    def record_failure(self, *, reason: str, signature: Optional[str], task_id: Optional[str]) -> None:
        attribution = classify_failure(reason, signature=signature)
        payload = {"task_id": task_id, **attribution.to_dict()}
        self.append("failure_attribution", payload)
        self.store.write_json(self.latest_verdict_path, payload)

    def record_qa_report(self, qa_report: QaReport) -> None:
        finding_count = len(qa_report.findings)
        payload = {
            "task_id": qa_report.task_id,
            "status": qa_report.status,
            "failure_signature": qa_report.failure_signature,
            "finding_count": finding_count,
            "quality_grade": self.quality_grade(qa_report.status, finding_count),
            "review": qa_report.review,
            "backend": qa_report.backend,
            "frontend": qa_report.frontend,
        }
        self.append("qa_report", payload)
        self.store.write_json(self.latest_verdict_path, payload)

    def record_repair_attempt(self, *, task_id: str, repair_count: int, failure_signature: Optional[str]) -> None:
        self.append(
            "repair_attempt",
            {
                "task_id": task_id,
                "repair_count": repair_count,
                "failure_signature": failure_signature,
            },
        )
