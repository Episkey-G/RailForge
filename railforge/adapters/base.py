from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from railforge.core.models import AdapterResult, CommitGateResult, ContractSpec, QaReport, TaskItem, WorkspaceLayout


@dataclass
class AdapterInvocation:
    role: str
    backend: str
    workspace: str
    command: List[str]
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "backend": self.backend,
            "workspace": self.workspace,
            "command": list(self.command),
            "payload": dict(self.payload),
        }


class LeadWriterAdapter:
    def implement(
        self,
        layout: WorkspaceLayout,
        task: TaskItem,
        contract: ContractSpec,
        run_meta,
    ) -> AdapterResult:
        raise NotImplementedError

    def repair_notes(self, task: TaskItem, qa_report: QaReport) -> str:
        root_cause = "unknown"
        if qa_report.findings:
            root_cause = qa_report.findings[0].message
        return (
            "# Repair Notes - %s\n\n"
            "## Root Cause\n- %s\n\n"
            "## Plan\n- 修复当前任务失败原因\n- 保持 contract 边界不变\n\n"
            "## Verification\n%s\n"
            % (task.id, root_cause, "\n".join("- %s" % item for item in task.verification))
        )


class SpecialistAdapter:
    def review(self, task: TaskItem, qa_report: Optional[QaReport], contract: ContractSpec) -> AdapterResult:
        raise NotImplementedError


class GitAdapter:
    def create_commit(self, workspace: Path, message: str, files: Iterable[str]) -> CommitGateResult:
        raise NotImplementedError

    def inspect_workspace(self, workspace: Path) -> Dict[str, Any]:
        return {
            "available": False,
            "dirty": False,
            "head": None,
            "branch": None,
            "status": [],
            "reason": "inspect_workspace_not_implemented",
        }


class ShellAdapter:
    def run(self, workspace: Path, commands: List[str]):
        raise NotImplementedError


class PlaywrightAdapter:
    def summarize(self, workspace: Path):
        return {}


@dataclass
class HarnessServices:
    lead_writer: LeadWriterAdapter
    backend_specialist: SpecialistAdapter
    frontend_specialist: SpecialistAdapter
    git: GitAdapter
    shell: ShellAdapter
    playwright: PlaywrightAdapter
    backend_evaluator: Optional[SpecialistAdapter] = None
    frontend_evaluator: Optional[SpecialistAdapter] = None
    clarification_analyst: Optional[Any] = None
