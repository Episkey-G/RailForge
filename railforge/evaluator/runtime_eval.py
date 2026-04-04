from typing import List

from railforge.core.models import AdapterResult, PhaseEvaluationResult, QaFinding, TaskItem


class RuntimeEvaluator:
    def evaluate(self, task: TaskItem, implementation: AdapterResult) -> PhaseEvaluationResult:
        metadata = implementation.metadata
        raw_findings = metadata.get("runtime_findings", [])
        findings = []  # type: List[QaFinding]
        for item in raw_findings:
            if isinstance(item, QaFinding):
                findings.append(item)
            else:
                findings.append(QaFinding.from_dict(item))

        result = PhaseEvaluationResult(
            status=metadata.get("runtime_status", "passed"),
            summary=metadata.get("runtime_summary", "runtime verification passed"),
            findings=findings,
            details={"failure_signature": metadata.get("failure_signature")},
        )
        return result

