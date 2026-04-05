from __future__ import annotations

from typing import Any, Dict

from railforge.adapters.base import AdapterResult
from railforge.adapters.codeagent_wrapper import CodeagentWrapper
from railforge.adapters.role_router import RoleRouter


class ClarificationAnalystAdapter:
    def __init__(
        self,
        delegate: Any = None,
        role_name: str = "clarification_analyst",
        role_router: RoleRouter | None = None,
        wrapper: CodeagentWrapper | None = None,
    ) -> None:
        self.delegate = delegate
        self.role_name = role_name
        self.role_router = role_router or RoleRouter()
        self.wrapper = wrapper or CodeagentWrapper()

    def invoke(self, **kwargs: Dict[str, Any]) -> AdapterResult:
        if self.delegate and hasattr(self.delegate, "invoke"):
            return self.delegate.invoke(**kwargs)
        role = kwargs.get("role", self.role_name)
        workspace = kwargs.get("workspace", ".")
        prompt = kwargs.get("prompt", "")
        backend = self.role_router.driver_for_role(role)
        result = self.wrapper.run(
            role=role,
            backend=backend,
            workspace=workspace,
            prompt=prompt,
            payload=kwargs,
        )
        result.summary = result.summary or "%s analysis complete" % role
        return result
