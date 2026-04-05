from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .enums import RunState


@dataclass
class ProductSpec:
    title: str
    summary: str
    acceptance_criteria: List[str]
    constraints: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    decision_points: List[str] = field(default_factory=list)
    status: str = "draft"
    source_request: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductSpec":
        return cls(**data)


@dataclass
class TaskItem:
    id: str
    title: str
    status: str
    priority: str
    depends_on: List[str]
    allowed_paths: List[str]
    verification: List[str]
    repair_budget: int
    done_definition: List[str] = field(default_factory=list)
    risk_level: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskItem":
        return cls(**data)


@dataclass
class ContractSpec:
    task_id: str
    scope: List[str]
    non_scope: List[str]
    allowed_paths: List[str]
    verification: List[str]
    rollback: List[str]
    done_definition: List[str]
    task_context: List[str] = field(default_factory=list)
    writeback_requirements: Dict[str, Any] = field(default_factory=dict)
    role_boundaries: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContractSpec":
        return cls(
            task_id=data["task_id"],
            scope=data.get("scope", []),
            non_scope=data.get("non_scope", []),
            allowed_paths=data.get("allowed_paths", []),
            verification=data.get("verification", []),
            rollback=data.get("rollback", []),
            done_definition=data.get("done_definition", []),
            task_context=data.get("task_context", []),
            writeback_requirements=data.get("writeback_requirements", {}),
            role_boundaries=data.get("role_boundaries", {}),
        )


@dataclass
class QaFinding:
    severity: str
    source: str
    message: str
    evidence: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "QaFinding":
        return cls(**data)


@dataclass
class PhaseEvaluationResult:
    status: str
    summary: str
    findings: List[QaFinding] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QaReport:
    task_id: str
    status: str
    static: Dict[str, str]
    runtime: Dict[str, str]
    outcome: Dict[str, str]
    findings: List[QaFinding] = field(default_factory=list)
    failure_signature: Optional[str] = None
    confidence_score: float = 0.0
    backend: Dict[str, Any] = field(default_factory=dict)
    frontend: Dict[str, Any] = field(default_factory=dict)
    review: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "static": self.static,
            "runtime": self.runtime,
            "outcome": self.outcome,
            "backend": self.backend,
            "frontend": self.frontend,
            "review": self.review,
            "findings": [finding.to_dict() for finding in self.findings],
            "failure_signature": self.failure_signature,
            "confidence_score": self.confidence_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QaReport":
        findings = [QaFinding.from_dict(item) for item in data.get("findings", [])]
        return cls(
            task_id=data["task_id"],
            status=data["status"],
            static=data.get("static", {}),
            runtime=data.get("runtime", {}),
            outcome=data.get("outcome", {}),
            backend=data.get("backend", {}),
            frontend=data.get("frontend", {}),
            review=data.get("review", {}),
            findings=findings,
            failure_signature=data.get("failure_signature"),
            confidence_score=data.get("confidence_score", 0.0),
        )


@dataclass
class AdapterResult:
    success: bool
    summary: str
    changed_files: List[str] = field(default_factory=list)
    proposed_patch: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RunMeta:
    run_id: str
    state: RunState
    current_task_id: Optional[str] = None
    repair_count: int = 0
    last_failure_signature: Optional[str] = None
    blocked_reason: Optional[str] = None
    resume_from_state: Optional[str] = None
    commit_log: List[Dict[str, Any]] = field(default_factory=list)
    checkpoint_index: int = 0
    thread_id: Optional[str] = None
    checkpoint_ref: Optional[str] = None
    project_name: str = ""
    request_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["state"] = self.state.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RunMeta":
        return cls(
            run_id=data["run_id"],
            state=RunState(data["state"]),
            current_task_id=data.get("current_task_id"),
            repair_count=data.get("repair_count", 0),
            last_failure_signature=data.get("last_failure_signature"),
            blocked_reason=data.get("blocked_reason"),
            resume_from_state=data.get("resume_from_state"),
            commit_log=data.get("commit_log", []),
            checkpoint_index=data.get("checkpoint_index", 0),
            thread_id=data.get("thread_id"),
            checkpoint_ref=data.get("checkpoint_ref"),
            project_name=data.get("project_name", ""),
            request_text=data.get("request_text", ""),
        )


@dataclass
class CheckpointRecord:
    sequence: int
    state: RunState
    path: Path
    langgraph: Dict[str, str] = field(default_factory=dict)


@dataclass
class RepairDecision:
    blocked: bool
    reason: Optional[str]


@dataclass
class BlockerDecision:
    blocked: bool
    reason: Optional[str]
    resume_from_state: Optional[str]


@dataclass
class CommitGateResult:
    passed: bool
    message: str
    dry_run: bool
    commit_hash: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkspaceLayout:
    root: Path

    @property
    def rf(self) -> Path:
        return self.root / ".railforge"

    @property
    def runtime(self) -> Path:
        return self.rf / "runtime"

    @property
    def runtime_router(self):
        from railforge.runtime import RuntimeArtifactRouter

        return RuntimeArtifactRouter(self)

    @property
    def docs(self) -> Path:
        return self.root / "docs"

    @property
    def product_dir(self) -> Path:
        return self.docs / "product-specs" / "active"

    @property
    def planning_dir(self) -> Path:
        return self.docs / "exec-plans" / "active"

    @property
    def execution_dir(self) -> Path:
        return self.runtime / "execution"

    @property
    def quality_dir(self) -> Path:
        return self.docs / "quality" / "active"

    @property
    def observability_dir(self) -> Path:
        return self.runtime / "observability"

    @property
    def context_dir(self) -> Path:
        return self.observability_dir / "context"

    @property
    def ledgers_dir(self) -> Path:
        return self.observability_dir / "ledgers"

    @property
    def codex_dir(self) -> Path:
        return self.root / ".codex"

    @property
    def codex_agents_dir(self) -> Path:
        return self.codex_dir / "agents"

    @property
    def codex_hooks_path(self) -> Path:
        return self.codex_dir / "hooks.json"

    @property
    def codex_config_path(self) -> Path:
        return self.codex_dir / "config.toml"

    @property
    def skills_dir(self) -> Path:
        return self.root / ".agents" / "skills"

    @property
    def legacy_product_dir(self) -> Path:
        return self.rf / "product"

    @property
    def legacy_planning_dir(self) -> Path:
        return self.rf / "planning"

    @property
    def legacy_execution_dir(self) -> Path:
        return self.rf / "execution"

    @property
    def task_reports_dir(self) -> Path:
        return self.execution_dir / "task_reports"

    @property
    def tasks(self) -> Path:
        run_id = self.runtime_router.active_run_id()
        if run_id:
            return self.runtime_router.tasks_dir(run_id)
        return self.runtime_router.runs_dir

    @property
    def checkpoints(self) -> Path:
        run_id = self.runtime_router.active_run_id()
        if run_id:
            return self.runtime_router.checkpoint_dir(run_id)
        return self.runtime_router.checkpoints_dir

    @property
    def langgraph_dir(self) -> Path:
        return self.runtime / "langgraph"

    @property
    def approvals(self) -> Path:
        run_id = self.runtime_router.active_run_id()
        if run_id:
            return self.runtime_router.approval_dir(run_id)
        return self.runtime_router.approvals_dir

    @property
    def interrupts(self) -> Path:
        run_id = self.runtime_router.active_run_id()
        if run_id:
            return self.runtime_router.blocked_interrupt_path(run_id).parent
        return self.runtime / "interrupts"

    @property
    def run_state_path(self) -> Path:
        return self.runtime_router.current_run_path

    @property
    def policies_path(self) -> Path:
        return self.runtime / "policies.yaml"

    @property
    def models_path(self) -> Path:
        return self.runtime / "models.yaml"

    @property
    def progress_path(self) -> Path:
        run_id = self.runtime_router.active_run_id()
        if run_id:
            return self.runtime_router.progress_path(run_id)
        return self.runtime / "progress.md"

    @property
    def product_spec_draft_path(self) -> Path:
        return self.product_dir / "product_spec.draft.yaml"

    @property
    def product_spec_path(self) -> Path:
        return self.product_dir / "product_spec.yaml"

    @property
    def product_spec_markdown_path(self) -> Path:
        return self.product_dir / "product_spec.md"

    @property
    def questions_path(self) -> Path:
        return self.product_dir / "questions.yaml"

    @property
    def answers_path(self) -> Path:
        return self.product_dir / "answers.yaml"

    @property
    def decisions_path(self) -> Path:
        return self.product_dir / "decisions.yaml"

    @property
    def backlog_draft_path(self) -> Path:
        return self.planning_dir / "backlog.draft.yaml"

    @property
    def backlog_path(self) -> Path:
        return self.planning_dir / "backlog.yaml"

    @property
    def planning_contract_path(self) -> Path:
        return self.planning_dir / "contract.yaml"

    def task_dir(self, task_id: str, run_id: Optional[str] = None) -> Path:
        return self.runtime_router.task_dir(task_id, run_id)

    def task_reviews_dir(self, task_id: str, run_id: Optional[str] = None) -> Path:
        return self.runtime_router.review_dir(task_id, run_id)

    def task_proposals_dir(self, task_id: str, run_id: Optional[str] = None) -> Path:
        return self.runtime_router.proposal_dir(task_id, run_id)

    def task_logs_dir(self, task_id: str, run_id: Optional[str] = None) -> Path:
        return self.runtime_router.note_dir(task_id, run_id) / "logs"

    def task_traces_dir(self, task_id: str, run_id: Optional[str] = None) -> Path:
        return self.runtime_router.trace_dir(task_id, run_id)

    @property
    def hosted_execution_request_path(self) -> Path:
        raise AttributeError("hosted_execution_request_path requires task_id; use layout.runtime_router.execution_request_path()")

    @property
    def hosted_execution_result_path(self) -> Path:
        raise AttributeError("hosted_execution_result_path requires task_id; use layout.runtime_router.execution_result_path()")

    @property
    def final_review_path(self) -> Path:
        return self.quality_dir / "final_review.json"

    @property
    def final_review_markdown_path(self) -> Path:
        return self.quality_dir / "final_review.md"

    @property
    def legacy_final_review_path(self) -> Path:
        return self.legacy_execution_dir / "final_review.json"

    @property
    def legacy_final_review_markdown_path(self) -> Path:
        return self.legacy_execution_dir / "final_review.md"

    def approval_path(self, target: str, task_id: Optional[str] = None) -> Path:
        return self.runtime_router.approval_path(target, task_id)

    def context_pack_path(self, phase: str) -> Path:
        return self.context_dir / ("%s.json" % phase)

    def ensure(self, task_id: Optional[str] = None) -> None:
        self.rf.mkdir(parents=True, exist_ok=True)
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.docs.mkdir(parents=True, exist_ok=True)
        self.product_dir.mkdir(parents=True, exist_ok=True)
        self.planning_dir.mkdir(parents=True, exist_ok=True)
        self.execution_dir.mkdir(parents=True, exist_ok=True)
        self.quality_dir.mkdir(parents=True, exist_ok=True)
        self.task_reports_dir.mkdir(parents=True, exist_ok=True)
        self.langgraph_dir.mkdir(parents=True, exist_ok=True)
        self.observability_dir.mkdir(parents=True, exist_ok=True)
        self.context_dir.mkdir(parents=True, exist_ok=True)
        self.ledgers_dir.mkdir(parents=True, exist_ok=True)
        self.runtime_router.ensure_roots()
        run_id = self.runtime_router.active_run_id()
        if run_id:
            self.runtime_router.ensure_roots(run_id=run_id, task_id=task_id)
