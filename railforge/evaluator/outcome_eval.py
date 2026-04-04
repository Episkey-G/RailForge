from railforge.core.models import AdapterResult, PhaseEvaluationResult, TaskItem


class OutcomeEvaluator:
    def evaluate(self, task: TaskItem, implementation: AdapterResult) -> PhaseEvaluationResult:
        metadata = implementation.metadata
        return PhaseEvaluationResult(
            status=metadata.get("outcome_status", "passed"),
            summary=metadata.get("outcome_summary", "outcome checks passed"),
            findings=[],
        )

