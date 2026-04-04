from __future__ import annotations

import json
from typing import Any, Dict

from railforge.adapters.base import AdapterResult, SpecialistAdapter
from railforge.adapters.codeagent_wrapper import CodeagentWrapper
from railforge.adapters.role_router import RoleRouter


class ClaudeCliSpecialistAdapter(SpecialistAdapter):
    def __init__(
        self,
        delegate: Any = None,
        role_name: str = "backend_specialist",
        role_router: RoleRouter | None = None,
        wrapper: CodeagentWrapper | None = None,
    ) -> None:
        self.delegate = delegate
        self.role_name = role_name
        self.role_router = role_router or RoleRouter()
        self.wrapper = wrapper or CodeagentWrapper()

    def _build_prompt(self, kwargs: Dict[str, Any]) -> str:
        return (
            "你是 RailForge 的 %s（Claude/GLM5 路径）。\n"
            "请只做分析、评估或补丁建议，不直接越权扩 scope。\n\n"
            "请只输出 JSON，对象结构固定为：\n"
            '{"status":"passed|failed","summary":"...","findings":[{"severity":"critical|high|medium|low","source":"backend","message":"...","evidence":"..."}],"details":{"failure_signature":"..."}}\n\n'
            "上下文：\n%s\n"
            % (self.role_name, json.dumps(kwargs, ensure_ascii=False, indent=2))
        )

    def invoke(self, **kwargs: Dict[str, Any]) -> AdapterResult:
        if self.delegate and hasattr(self.delegate, "invoke"):
            return self.delegate.invoke(**kwargs)
        task = kwargs.get("task", {})
        task_id = task.get("id", "unknown")
        role = kwargs.get("role", self.role_name)
        workspace = kwargs.get("workspace", ".")
        backend = self.role_router.driver_for_role(role)
        result = self.wrapper.run(
            role=role,
            backend=backend,
            workspace=workspace,
            prompt=self._build_prompt(kwargs),
            payload=kwargs,
        )
        result.summary = result.summary or "claude review for %s" % task_id
        return result

    def review(self, task, qa_report, contract) -> AdapterResult:
        if self.delegate and hasattr(self.delegate, "review"):
            return self.delegate.review(task, qa_report, contract)
        return self.invoke(
            role=self.role_name,
            workspace=".",
            task=task.to_dict(),
            qa_report=qa_report.to_dict() if qa_report else None,
            contract=contract.to_dict(),
        )
