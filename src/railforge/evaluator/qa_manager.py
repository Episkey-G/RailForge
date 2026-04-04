from typing import Iterable, List

from railforge.core.models import PhaseEvaluationResult, QaFinding, QaReport, TaskItem


def _coerce_phase(value):
    if isinstance(value, PhaseEvaluationResult):
        return value
    return PhaseEvaluationResult(
        status=value.get("status", "passed"),
        summary=value.get("summary", ""),
        findings=[],
    )


class QaManager:
    def build_report(
        self,
        task: TaskItem,
        static_status,
        runtime_status,
        outcome_status,
        findings: Iterable[QaFinding],
        failure_signature,
    ) -> QaReport:
        static_phase = _coerce_phase(static_status)
        runtime_phase = _coerce_phase(runtime_status)
        outcome_phase = _coerce_phase(outcome_status)
        all_findings = list(findings)
        status = "approved"
        if (
            static_phase.status != "passed"
            or runtime_phase.status != "passed"
            or outcome_phase.status != "passed"
            or all_findings
        ):
            status = "failed"
        return QaReport(
            task_id=task.id,
            status=status,
            static={"status": static_phase.status, "summary": static_phase.summary},
            runtime={"status": runtime_phase.status, "summary": runtime_phase.summary},
            outcome={"status": outcome_phase.status, "summary": outcome_phase.summary},
            findings=all_findings,
            failure_signature=failure_signature,
            confidence_score=1.0 if status == "approved" else 0.35,
        )

    def aggregate(
        self,
        task: TaskItem,
        static_phase: PhaseEvaluationResult,
        runtime_phase: PhaseEvaluationResult,
        outcome_phase: PhaseEvaluationResult,
    ) -> QaReport:
        findings = []  # type: List[QaFinding]
        findings.extend(static_phase.findings)
        findings.extend(runtime_phase.findings)
        findings.extend(outcome_phase.findings)
        failure_signature = runtime_phase.details.get("failure_signature") or outcome_phase.details.get("failure_signature")
        return self.build_report(
            task=task,
            static_status=static_phase,
            runtime_status=runtime_phase,
            outcome_status=outcome_phase,
            findings=findings,
            failure_signature=failure_signature,
        )

