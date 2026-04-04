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
    def docs(self) -> Path:
        return self.root / "docs"

    @property
    def product_dir(self) -> Path:
        return self.rf / "product"

    @property
    def planning_dir(self) -> Path:
        return self.rf / "planning"

    @property
    def execution_dir(self) -> Path:
        return self.rf / "execution"

    @property
    def task_reports_dir(self) -> Path:
        return self.execution_dir / "task_reports"

    @property
    def tasks(self) -> Path:
        return self.execution_dir / "tasks"

    @property
    def checkpoints(self) -> Path:
        return self.runtime / "checkpoints"

    @property
    def langgraph_dir(self) -> Path:
        return self.runtime / "langgraph"

    @property
    def approvals(self) -> Path:
        return self.runtime / "approvals"

    @property
    def interrupts(self) -> Path:
        return self.runtime / "interrupts"

    @property
    def run_state_path(self) -> Path:
        return self.runtime / "run_state.json"

    @property
    def policies_path(self) -> Path:
        return self.runtime / "policies.yaml"

    @property
    def models_path(self) -> Path:
        return self.runtime / "models.yaml"

    @property
    def progress_path(self) -> Path:
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

    def task_dir(self, task_id: str) -> Path:
        return self.tasks / task_id

    def task_reviews_dir(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "reviews"

    def task_proposals_dir(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "proposals"

    def task_logs_dir(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "logs"

    def task_traces_dir(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "traces"

    @property
    def hosted_execution_request_path(self) -> Path:
        return self.runtime / "hosted_execution_request.json"

    @property
    def hosted_execution_result_path(self) -> Path:
        return self.runtime / "hosted_execution_result.json"

    @property
    def final_review_path(self) -> Path:
        return self.execution_dir / "final_review.json"

    @property
    def final_review_markdown_path(self) -> Path:
        return self.execution_dir / "final_review.md"

    def approval_path(self, target: str, task_id: Optional[str] = None) -> Path:
        name = target if not task_id else "%s-%s" % (target, task_id)
        return self.approvals / ("%s.json" % name)

    def ensure(self, task_id: Optional[str] = None) -> None:
        self.rf.mkdir(parents=True, exist_ok=True)
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.product_dir.mkdir(parents=True, exist_ok=True)
        self.planning_dir.mkdir(parents=True, exist_ok=True)
        self.execution_dir.mkdir(parents=True, exist_ok=True)
        self.task_reports_dir.mkdir(parents=True, exist_ok=True)
        self.tasks.mkdir(parents=True, exist_ok=True)
        self.checkpoints.mkdir(parents=True, exist_ok=True)
        self.langgraph_dir.mkdir(parents=True, exist_ok=True)
        self.approvals.mkdir(parents=True, exist_ok=True)
        self.interrupts.mkdir(parents=True, exist_ok=True)
        if task_id:
            self.task_dir(task_id).mkdir(parents=True, exist_ok=True)
            self.task_reviews_dir(task_id).mkdir(parents=True, exist_ok=True)
            self.task_proposals_dir(task_id).mkdir(parents=True, exist_ok=True)
            self.task_logs_dir(task_id).mkdir(parents=True, exist_ok=True)
            self.task_traces_dir(task_id).mkdir(parents=True, exist_ok=True)
