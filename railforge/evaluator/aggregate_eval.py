from __future__ import annotations

from typing import Any, Mapping

from railforge.core.models import PhaseEvaluationResult, QaFinding


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if hasattr(value, "__dict__"):
        return vars(value)
    raise TypeError(f"unsupported evaluation payload: {type(value)!r}")


def coerce_finding(value: Any) -> QaFinding:
    if isinstance(value, QaFinding):
        return value
    payload = _as_mapping(value)
    return QaFinding.from_dict(dict(payload))


def coerce_phase_result(value: Any) -> PhaseEvaluationResult:
    if isinstance(value, PhaseEvaluationResult):
        return value
    if value is None:
        return PhaseEvaluationResult(status="passed", summary="")

    payload = _as_mapping(value)
    raw_findings = payload.get("findings", [])
    findings = [coerce_finding(item) for item in raw_findings]
    details = payload.get("details", {})
    if not isinstance(details, dict):
        details = dict(_as_mapping(details))
    return PhaseEvaluationResult(
        status=payload.get("status", "passed"),
        summary=payload.get("summary", ""),
        findings=findings,
        details=details,
    )


class AggregateEvaluator:
    def merge(self, backend_status: Any, frontend_status: Any) -> PhaseEvaluationResult:
        backend_phase = coerce_phase_result(backend_status)
        frontend_phase = coerce_phase_result(frontend_status)

        findings = [*backend_phase.findings, *frontend_phase.findings]
        critical_finding = next((finding for finding in findings if finding.severity == "critical"), None)
        backend_failed = backend_phase.status != "passed"
        frontend_failed = frontend_phase.status != "passed"
        has_findings = bool(findings)
        failed = critical_finding is not None or backend_failed or frontend_failed or has_findings

        if critical_finding is not None:
            summary = f"critical finding detected: {critical_finding.message}"
        elif backend_failed and frontend_failed:
            summary = "backend and frontend evaluators failed"
        elif backend_failed:
            summary = "backend evaluator failed"
        elif frontend_failed:
            summary = "frontend evaluator failed"
        elif has_findings:
            summary = "dual evaluation found issues"
        else:
            summary = "backend and frontend evaluators passed"

        details = {
            "backend": {
                "status": backend_phase.status,
                "summary": backend_phase.summary,
                "findings": [finding.to_dict() for finding in backend_phase.findings],
            },
            "frontend": {
                "status": frontend_phase.status,
                "summary": frontend_phase.summary,
                "findings": [finding.to_dict() for finding in frontend_phase.findings],
            },
        }
        failure_signature = backend_phase.details.get("failure_signature") or frontend_phase.details.get("failure_signature")
        if failure_signature is not None:
            details["failure_signature"] = failure_signature
        if critical_finding is not None:
            details["critical_finding"] = critical_finding.to_dict()

        return PhaseEvaluationResult(
            status="failed" if failed else "passed",
            summary=summary,
            findings=findings,
            details=details,
        )

