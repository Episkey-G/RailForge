from __future__ import annotations

from typing import Any, Dict

from railforge.adapters.base import LeadWriterAdapter
from railforge.core.models import AdapterResult


class CodexCliLeadWriterAdapter(LeadWriterAdapter):
    def __init__(self, delegate: Any = None) -> None:
        self.delegate = delegate

    def invoke(self, **kwargs: Dict[str, Any]) -> AdapterResult:
        if self.delegate and hasattr(self.delegate, "invoke"):
            return self.delegate.invoke(**kwargs)
        task = kwargs.get("task", {})
        task_id = task.get("id", "unknown")
        return AdapterResult(success=True, summary="codex dry-run for %s" % task_id, metadata={"structured": kwargs})

    def implement(self, layout, task, contract, run_meta) -> AdapterResult:
        if self.delegate and hasattr(self.delegate, "implement"):
            return self.delegate.implement(layout, task, contract, run_meta)
        return self.invoke(
            workspace=str(layout.root),
            task=task.to_dict(),
            contract=contract.to_dict(),
            run_meta=run_meta.to_dict(),
        )
