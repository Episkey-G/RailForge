from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentRequest:
    backend: str
    role: str
    workspace: str
    prompt: str
    payload: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    model: Optional[str] = None
    reasoning_effort: Optional[str] = None
    timeout_seconds: Optional[int] = None


@dataclass
class ParsedOutput:
    summary: str
    structured: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None


@dataclass
class ExecutionDiagnostics:
    command: List[str]
    returncode: int
    duration_ms: int
    timed_out: bool = False
    killed: bool = False
    backend: str = ""
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentResponse:
    success: bool
    backend: str
    role: str
    summary: str
    stdout: str = ""
    stderr: str = ""
    structured: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    diagnostics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
