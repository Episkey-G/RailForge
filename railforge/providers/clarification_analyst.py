from __future__ import annotations

from typing import Any

from railforge.adapters.base import AdapterResult
from railforge.integrations.codeagent import CodeagentWrapper
from railforge.providers.role_router import RoleRouter


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

    def invoke(self, **kwargs: dict[str, Any]) -> AdapterResult:
        if self.delegate and hasattr(self.delegate, "invoke"):
            return self.delegate.invoke(**kwargs)
        role = kwargs.get("role", self.role_name)
        workspace = kwargs.get("workspace", ".")
        prompt = kwargs.get("prompt", "")
        profile = self.role_router.profile_for_role(role)
        result = self.wrapper.run(
            role=role,
            backend=profile.backend,
            workspace=workspace,
            prompt=prompt,
            payload={
                **kwargs,
                "role_policy": profile.to_dict(),
            },
        )
        result.summary = result.summary or "%s analysis complete" % role
        return result
