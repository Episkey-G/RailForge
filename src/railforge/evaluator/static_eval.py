from typing import Iterable, List

from railforge.core.models import AdapterResult, ContractSpec, PhaseEvaluationResult, QaFinding, TaskItem


class StaticEvaluator:
    def evaluate(
        self,
        task: TaskItem,
        contract: ContractSpec,
        implementation: AdapterResult,
        reviews: Iterable[AdapterResult],
    ) -> PhaseEvaluationResult:
        findings = []  # type: List[QaFinding]

        for changed_file in implementation.changed_files:
            if not any(changed_file.startswith(prefix) for prefix in contract.allowed_paths):
                findings.append(
                    QaFinding(
                        severity="critical",
                        source="static",
                        message="changed file is outside allowed_paths: %s" % changed_file,
                        evidence=changed_file,
                    )
                )

        for review in reviews:
            if review.metadata.get("blocker"):
                findings.append(
                    QaFinding(
                        severity="high",
                        source="review",
                        message="review blocker: %s" % review.summary,
                        evidence=review.summary,
                    )
                )

        status = "failed" if findings else "passed"
        summary = "static review passed" if not findings else "static review failed"
        return PhaseEvaluationResult(status=status, summary=summary, findings=findings)

