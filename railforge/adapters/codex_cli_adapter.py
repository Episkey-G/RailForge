from __future__ import annotations

import json
from typing import Any, Dict

from railforge.adapters.base import AdapterResult, LeadWriterAdapter
from railforge.adapters.codeagent_wrapper import CodeagentWrapper
from railforge.adapters.role_router import RoleRouter


class CodexCliLeadWriterAdapter(LeadWriterAdapter):
    def __init__(
        self,
        delegate: Any = None,
        role_router: RoleRouter | None = None,
        wrapper: CodeagentWrapper | None = None,
    ) -> None:
        self.delegate = delegate
        self.role_router = role_router or RoleRouter()
        self.wrapper = wrapper or CodeagentWrapper()

    @staticmethod
    def _build_prompt(kwargs: Dict[str, Any]) -> str:
        return (
            "你是 RailForge 的 lead writer（Codex）。\n"
            "严格遵守 contract 边界，只在允许目录内修改。\n\n"
            "上下文：\n"
            "%s\n"
            % json.dumps(kwargs, ensure_ascii=False, indent=2)
        )

    def invoke(self, **kwargs: Dict[str, Any]) -> AdapterResult:
        if self.delegate and hasattr(self.delegate, "invoke"):
            return self.delegate.invoke(**kwargs)
        task = kwargs.get("task", {})
        task_id = task.get("id", "unknown")
        role = kwargs.get("role", "lead_writer")
        workspace = kwargs.get("workspace", ".")
        backend = self.role_router.driver_for_role(role)
        result = self.wrapper.run(
            role=role,
            backend=backend,
            workspace=workspace,
            prompt=self._build_prompt(kwargs),
            payload=kwargs,
        )
        result.summary = result.summary or "codex execution for %s" % task_id
        return result

    def implement(self, layout, task, contract, run_meta) -> AdapterResult:
        if self.delegate and hasattr(self.delegate, "implement"):
            return self.delegate.implement(layout, task, contract, run_meta)
        return self.invoke(
            role="lead_writer",
            workspace=str(layout.root),
            task=task.to_dict(),
            contract=contract.to_dict(),
            run_meta=run_meta.to_dict(),
        )
