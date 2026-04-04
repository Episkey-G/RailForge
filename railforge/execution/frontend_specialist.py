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


def _annotate_result(result: AdapterResult, role: str, writable_paths: list[str]) -> AdapterResult:
    attempted_writes = list(result.changed_files)
    boundary_violations = [
        path for path in attempted_writes if not any(path.startswith(prefix) for prefix in writable_paths)
    ]
    metadata = dict(result.metadata)
    metadata["trace"] = {
        "role": role,
        "read_only": True,
        "allowed_write_paths": list(writable_paths),
        "attempted_writes": attempted_writes,
        "boundary_violations": boundary_violations,
        "summary": result.summary,
    }
    return AdapterResult(
        success=result.success,
        summary=result.summary,
        changed_files=attempted_writes,
        proposed_patch=result.proposed_patch,
        metadata=metadata,
    )


class FrontendSpecialistService:
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
                role="frontend_specialist",
                workspace=str(layout.root),
                task=task.to_dict(),
                contract=contract.to_dict(),
                qa_report=qa_report.to_dict() if qa_report else None,
                writable_paths=writable_paths,
            )
            return _annotate_result(_coerce_result(result), "frontend_specialist", writable_paths)
        return _annotate_result(
            self.adapter.review(task=task, qa_report=qa_report, contract=contract),
            "frontend_specialist",
            writable_paths,
        )
