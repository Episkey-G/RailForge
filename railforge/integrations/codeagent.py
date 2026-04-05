from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from railforge.adapters.base import AdapterInvocation
from railforge.codeagent.service import CodeagentService
from railforge.core.models import AdapterResult


class CodeagentWrapper:
    def __init__(self, binary: str = "python", dry_run: bool = True) -> None:
        self.binary = binary
        self.dry_run = dry_run
        self.service = CodeagentService(dry_run=dry_run)

    def build_command(self, backend: str, workspace: str | Path) -> list[str]:
        return [
            self.binary,
            "-m",
            "railforge.codeagent",
            "run",
            "--backend",
            backend,
            "--workspace",
            str(workspace),
        ]

    def build_invocation(
        self,
        *,
        role: str,
        backend: str,
        workspace: str | Path,
        payload: Mapping[str, Any] | None = None,
    ) -> AdapterInvocation:
        command = self.build_command(backend=backend, workspace=workspace)
        return AdapterInvocation(
            role=role,
            backend=backend,
            workspace=str(workspace),
            command=command,
            payload=dict(payload or {}),
        )

    def run(
        self,
        *,
        role: str,
        backend: str,
        workspace: str | Path,
        prompt: str,
        payload: Mapping[str, Any] | None = None,
    ) -> AdapterResult:
        invocation = self.build_invocation(
            role=role,
            backend=backend,
            workspace=workspace,
            payload=payload,
        )
        response = self.service.run(
            backend=backend,
            role=role,
            workspace=str(workspace),
            prompt=prompt,
            payload=dict(payload or {}),
        )
        return AdapterResult(
            success=response.success,
            summary=response.summary,
            metadata={
                "structured": response.structured,
                "invocation": invocation.to_dict(),
                "returncode": response.diagnostics.get("returncode", 0),
                "stdout": response.stdout,
                "stderr": response.stderr,
                "session_id": response.session_id,
                "diagnostics": response.diagnostics,
            },
        )
