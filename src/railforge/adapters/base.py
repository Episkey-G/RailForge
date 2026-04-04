from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from railforge.core.models import AdapterResult, CommitGateResult, ContractSpec, QaReport, TaskItem, WorkspaceLayout


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

