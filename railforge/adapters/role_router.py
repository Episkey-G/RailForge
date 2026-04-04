from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from railforge.adapters.base import AdapterInvocation
from railforge.adapters.codeagent_wrapper import CodeagentWrapper
from railforge.core.models import WorkspaceLayout

import yaml


class RoleRouter:
    DEFAULT_ROLE_BACKENDS = {
        "lead_writer": "hosted_codex",
        "backend_specialist": "claude_cli",
        "frontend_specialist": "gemini_cli",
        "backend_evaluator": "claude_cli",
        "frontend_evaluator": "gemini_cli",
    }

    def __init__(
        self,
        role_backends: Mapping[str, str] | None = None,
        wrapper: CodeagentWrapper | None = None,
    ) -> None:
        self.role_backends = dict(self.DEFAULT_ROLE_BACKENDS)
        if role_backends:
            self.role_backends.update(role_backends)
        self.wrapper = wrapper or CodeagentWrapper()

    def driver_for_role(self, role: str) -> str:
        if role not in self.role_backends:
            raise KeyError(f"Unknown role: {role}")
        return self.role_backends[role]

    def backend_for_role(self, role: str) -> str:
        return self.driver_for_role(role)

    def route(
        self,
        *,
        role: str,
        workspace: str | Path,
        payload: Mapping[str, Any] | None = None,
    ) -> AdapterInvocation:
        backend = self.driver_for_role(role)
        return self.wrapper.build_invocation(
            role=role,
            backend=backend,
            workspace=workspace,
            payload=payload,
        )


def load_role_backends(workspace: Path) -> dict[str, str]:
    layout = WorkspaceLayout(workspace)
    if not layout.models_path.exists():
        return dict(RoleRouter.DEFAULT_ROLE_BACKENDS)
    payload = yaml.safe_load(layout.models_path.read_text(encoding="utf-8")) or {}
    roles = payload.get("roles", {})
    result = dict(RoleRouter.DEFAULT_ROLE_BACKENDS)
    for role, config in roles.items():
        driver = config.get("driver") or config.get("adapter")
        if driver:
            result[role] = driver
    return result
