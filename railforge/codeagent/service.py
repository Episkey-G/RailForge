from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional

from railforge.codeagent.backends.claude import build_claude_command
from railforge.codeagent.backends.codex import build_codex_command
from railforge.codeagent.backends.gemini import build_gemini_command
from railforge.codeagent.compatibility import normalize_backend_name, normalize_reasoning_effort
from railforge.codeagent.diagnostics import build_diagnostics
from railforge.codeagent.models import AgentRequest, AgentResponse
from railforge.codeagent.parser import parse_agent_output
from railforge.codeagent.sessions import backend_supports_resume
from railforge.codeagent.timeouts import timeout_for_backend


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


class CodeagentService:
    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run

    def build_request(
        self,
        *,
        backend: str,
        role: str,
        workspace: str,
        prompt: str,
        payload: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> AgentRequest:
        payload = dict(payload or {})
        resolved_backend = normalize_backend_name(backend)
        request_model = model or payload.get("model")
        request_effort = reasoning_effort or payload.get("reasoning_effort") or payload.get("model_reasoning_effort")
        request_timeout = timeout_seconds or payload.get("timeout_seconds") or timeout_for_backend(resolved_backend)
        return AgentRequest(
            backend=resolved_backend,
            role=role,
            workspace=workspace,
            prompt=prompt,
            payload=payload,
            session_id=session_id,
            model=request_model,
            reasoning_effort=normalize_reasoning_effort(resolved_backend, request_effort),
            timeout_seconds=int(request_timeout),
        )

    def run(
        self,
        *,
        backend: str,
        role: str,
        workspace: str,
        prompt: str,
        payload: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> AgentResponse:
        request = self.build_request(
            backend=backend,
            role=role,
            workspace=workspace,
            prompt=prompt,
            payload=payload,
            model=model,
            reasoning_effort=reasoning_effort,
            timeout_seconds=timeout_seconds,
        )
        return self._execute_backend(request)

    def resume(
        self,
        *,
        backend: str,
        role: str,
        workspace: str,
        session_id: str,
        prompt: str,
        payload: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> AgentResponse:
        request = self.build_request(
            backend=backend,
            role=role,
            workspace=workspace,
            prompt=prompt,
            payload=payload,
            session_id=session_id,
            model=model,
            reasoning_effort=reasoning_effort,
            timeout_seconds=timeout_seconds,
        )
        if not backend_supports_resume(backend):
            return self._execute_backend(request)
        return self._execute_backend(request)

    def probe(self, *, backend: str, workspace: str) -> AgentResponse:
        return self.run(
            backend=backend,
            role="probe",
            workspace=workspace,
            prompt="请只返回 ok",
            payload={"probe": True},
        )

    def _runner_for(self, backend: str):
        if backend == "codex":
            return build_codex_command
        if backend == "claude":
            return build_claude_command
        if backend == "gemini":
            return build_gemini_command
        raise KeyError(f"Unsupported backend: {backend}")

    def _command_for(self, request: AgentRequest) -> list[str]:
        if request.backend == "codex":
            return build_codex_command(
                workspace=request.workspace,
                model=request.model,
                reasoning_effort=request.reasoning_effort,
            )
        if request.backend == "claude":
            return build_claude_command(prompt=request.prompt, session_id=request.session_id)
        if request.backend == "gemini":
            return build_gemini_command(
                workspace=request.workspace,
                prompt=request.prompt,
                session_id=request.session_id,
            )
        raise KeyError(f"Unsupported backend: {request.backend}")

    def _stdin_for(self, request: AgentRequest) -> Optional[str]:
        if request.backend == "codex":
            return request.prompt
        return None

    def _spawn_process(
        self,
        command: list[str],
        *,
        input_text: Optional[str],
        timeout_seconds: int,
        workspace: str,
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            command,
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
            cwd=workspace,
        )

    def _dry_run_response(self, request: AgentRequest, command: list[str]) -> AgentResponse:
        diagnostics = build_diagnostics(
            command=command,
            returncode=0,
            duration_ms=0,
            backend=request.backend,
        )
        return AgentResponse(
            success=True,
            backend=request.backend,
            role=request.role,
            summary=f"{request.role} dry-run via railforge.codeagent",
            structured=request.payload,
            diagnostics=diagnostics,
        )

    def _execute_backend(self, request: AgentRequest) -> AgentResponse:
        command = self._command_for(request)
        if self.dry_run:
            return self._dry_run_response(request, command)

        Path(request.workspace).mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        try:
            completed = self._spawn_process(
                command,
                input_text=self._stdin_for(request),
                timeout_seconds=request.timeout_seconds or timeout_for_backend(request.backend),
                workspace=request.workspace,
            )
        except subprocess.TimeoutExpired as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            stdout = _coerce_text(exc.stdout)
            stderr = _coerce_text(exc.stderr)
            diagnostics = build_diagnostics(
                command=command,
                returncode=-1,
                duration_ms=duration_ms,
                backend=request.backend,
                timed_out=True,
                killed=True,
                error="timeout",
            )
            return AgentResponse(
                success=False,
                backend=request.backend,
                role=request.role,
                summary=f"{request.backend} timed out",
                stdout=stdout,
                stderr=stderr,
                structured={"status": "failed", "summary": f"{request.backend} timed out"},
                diagnostics=diagnostics,
            )

        duration_ms = int((time.perf_counter() - started) * 1000)
        parsed = parse_agent_output(completed.stdout, completed.stderr)
        diagnostics = build_diagnostics(
            command=command,
            returncode=completed.returncode,
            duration_ms=duration_ms,
            backend=request.backend,
            error="" if completed.returncode == 0 else "backend_error",
        )
        return AgentResponse(
            success=completed.returncode == 0,
            backend=request.backend,
            role=request.role,
            summary=parsed.summary,
            stdout=completed.stdout,
            stderr=completed.stderr,
            structured=parsed.structured,
            session_id=parsed.session_id,
            diagnostics=diagnostics,
        )
