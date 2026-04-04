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

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContractSpec":
        return cls(**data)


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
    findings: List[QaFinding]
    failure_signature: Optional[str]
    confidence_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "static": self.static,
            "runtime": self.runtime,
            "outcome": self.outcome,
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
            project_name=data.get("project_name", ""),
            request_text=data.get("request_text", ""),
        )


@dataclass
class CheckpointRecord:
    sequence: int
    state: RunState
    path: Path


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
    def tasks(self) -> Path:
        return self.rf / "tasks"

    @property
    def checkpoints(self) -> Path:
        return self.rf / "checkpoints"

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

    def ensure(self, task_id: Optional[str] = None) -> None:
        self.rf.mkdir(parents=True, exist_ok=True)
        self.tasks.mkdir(parents=True, exist_ok=True)
        self.checkpoints.mkdir(parents=True, exist_ok=True)
        if task_id:
            self.task_dir(task_id).mkdir(parents=True, exist_ok=True)
            self.task_reviews_dir(task_id).mkdir(parents=True, exist_ok=True)
            self.task_proposals_dir(task_id).mkdir(parents=True, exist_ok=True)
            self.task_logs_dir(task_id).mkdir(parents=True, exist_ok=True)
            self.task_traces_dir(task_id).mkdir(parents=True, exist_ok=True)

