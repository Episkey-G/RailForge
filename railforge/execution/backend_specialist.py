from __future__ import annotations

from typing import Any, Optional

from railforge.core.models import AdapterResult, ContractSpec, QaReport, TaskItem, WorkspaceLayout


def _coerce_result(result: Any) -> AdapterResult:
    if isinstance(result, AdapterResult):
        return result
    if isinstance(result, dict):
        return AdapterResult(
            success=result.get("success", True),
            summary=result.get("summary", ""),
            changed_files=result.get("changed_files", []),
            proposed_patch=result.get("proposed_patch"),
            metadata=result.get("metadata", {}),
        )
    raise TypeError("unsupported adapter result: %r" % (result,))


class BackendSpecialistService:
    def __init__(self, adapter: Any) -> None:
        self.adapter = adapter

    def review(
        self,
        layout: WorkspaceLayout,
        task: TaskItem,
        contract: ContractSpec,
        qa_report: Optional[QaReport],
    ) -> AdapterResult:
        writable_paths = [
            str(layout.task_reviews_dir(task.id).relative_to(layout.root)) + "/",
            str(layout.task_proposals_dir(task.id).relative_to(layout.root)) + "/",
        ]
        if hasattr(self.adapter, "invoke"):
            result = self.adapter.invoke(
                role="backend_specialist",
                workspace=str(layout.root),
                task=task.to_dict(),
                contract=contract.to_dict(),
                qa_report=qa_report.to_dict() if qa_report else None,
                writable_paths=writable_paths,
            )
            return _coerce_result(result)
        return self.adapter.review(task=task, qa_report=qa_report, contract=contract)
