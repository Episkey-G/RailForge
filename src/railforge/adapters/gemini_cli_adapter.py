from __future__ import annotations

from typing import Any, Dict

from railforge.adapters.base import SpecialistAdapter
from railforge.core.models import AdapterResult


class GeminiCliSpecialistAdapter(SpecialistAdapter):
    def __init__(self, delegate: Any = None, role_name: str = "frontend_specialist") -> None:
        self.delegate = delegate
        self.role_name = role_name

    def invoke(self, **kwargs: Dict[str, Any]) -> AdapterResult:
        if self.delegate and hasattr(self.delegate, "invoke"):
            return self.delegate.invoke(**kwargs)
        task = kwargs.get("task", {})
        task_id = task.get("id", "unknown")
        return AdapterResult(
            success=True,
            summary="gemini dry-run review for %s via %s" % (task_id, self.role_name),
            proposed_patch="",
            metadata={"structured": kwargs},
        )

    def review(self, task, qa_report, contract) -> AdapterResult:
        if self.delegate and hasattr(self.delegate, "review"):
            return self.delegate.review(task, qa_report, contract)
        return self.invoke(task=task.to_dict(), qa_report=qa_report.to_dict() if qa_report else None, contract=contract.to_dict())
