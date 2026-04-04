from __future__ import annotations

from typing import Any, Dict, List

from railforge.core.models import AdapterResult, ContractSpec, RunMeta, TaskItem, WorkspaceLayout


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


class CodexWriterService:
    def __init__(self, adapter: Any) -> None:
        self.adapter = adapter

    def execute(
        self,
        layout: WorkspaceLayout,
        task: TaskItem,
        contract: ContractSpec,
        run_meta: RunMeta,
    ) -> AdapterResult:
        writable_paths = list(contract.allowed_paths) + [".railforge/tasks/%s/" % task.id]
        if hasattr(self.adapter, "invoke"):
            result = self.adapter.invoke(
                role="lead_writer",
                workspace=str(layout.root),
                task=task.to_dict(),
                contract=contract.to_dict(),
                run_meta=run_meta.to_dict(),
                writable_paths=writable_paths,
            )
            return _coerce_result(result)
        return self.adapter.implement(layout=layout, task=task, contract=contract, run_meta=run_meta)
