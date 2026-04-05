from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from railforge.core.errors import RailForgeError
from railforge.core.models import AdapterResult
from railforge.planner.clarification import ClarificationContractError, ClarificationOutcome, analyze_request
from railforge.planner.clarification_prompts import build_clarification_prompt


class ClarificationAnalysisError(RailForgeError):
    """Raised when AI-led clarification cannot produce a usable structured result."""


class ClarificationService:
    def __init__(self, adapter: Any) -> None:
        self.adapter = adapter

    def analyze(
        self,
        *,
        phase: str,
        project: str,
        request_text: str,
        answers: Dict[str, str],
        context: Optional[Dict[str, Any]] = None,
        previous_questions: Optional[Mapping[str, Any]] = None,
        workspace: str = ".",
    ) -> ClarificationOutcome:
        prompt = build_clarification_prompt(
            phase=phase,
            project=project,
            request_text=request_text,
            answers=answers,
            context=context or {},
        )
        result = self._invoke_adapter(
            phase=phase,
            workspace=workspace,
            prompt=prompt,
            payload={
                "project": project,
                "request_text": request_text,
                "answers": answers,
                "context": context or {},
                "phase": phase,
            },
        )
        structured = result.metadata.get("structured", {}) if isinstance(result, AdapterResult) else {}
        if not structured:
            raise ClarificationAnalysisError("clarification_analyst returned no structured payload")
        try:
            outcome = analyze_request(
                project=project,
                request_text=request_text,
                payload=structured,
                answers=answers,
                previous_questions=previous_questions,
            )
        except ClarificationContractError as exc:
            raise ClarificationAnalysisError(str(exc)) from exc
        outcome.trace["summary"] = result.summary
        outcome.trace["phase"] = phase
        outcome.trace["structured"] = structured
        outcome.trace["diagnostics"] = result.metadata.get("diagnostics", {})
        return outcome

    def _invoke_adapter(self, *, phase: str, workspace: str, prompt: str, payload: Dict[str, Any]) -> AdapterResult:
        if self.adapter is None:
            raise ClarificationAnalysisError("clarification_analyst is not configured")
        if hasattr(self.adapter, "invoke"):
            result = self.adapter.invoke(
                role="clarification_analyst",
                phase=phase,
                workspace=workspace,
                prompt=prompt,
                context=payload,
            )
            if isinstance(result, AdapterResult):
                return result
            if isinstance(result, dict):
                return AdapterResult(
                    success=result.get("success", True),
                    summary=result.get("summary", ""),
                    metadata=result.get("metadata", {}),
                )
        raise ClarificationAnalysisError("clarification_analyst does not support invoke()")
