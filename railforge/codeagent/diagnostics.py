from __future__ import annotations

from railforge.codeagent.models import ExecutionDiagnostics


def build_diagnostics(
    *,
    command: list[str],
    returncode: int,
    duration_ms: int,
    backend: str,
    timed_out: bool = False,
    killed: bool = False,
    error: str = "",
) -> dict:
    diagnostics = ExecutionDiagnostics(
        command=command,
        returncode=returncode,
        duration_ms=duration_ms,
        timed_out=timed_out,
        killed=killed,
        backend=backend,
        error=error,
    )
    return diagnostics.to_dict()
