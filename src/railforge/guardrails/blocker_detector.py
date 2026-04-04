from railforge.core.models import BlockerDecision, RunMeta, TaskItem


def detect_blocker(run: RunMeta, task: TaskItem, repeated_failure: bool = False) -> BlockerDecision:
    if run.repair_count >= task.repair_budget:
        return BlockerDecision(
            blocked=True,
            reason="repair_budget_exhausted",
            resume_from_state="IMPLEMENTING",
        )
    if repeated_failure:
        return BlockerDecision(
            blocked=True,
            reason="repeated_failure_signature",
            resume_from_state="IMPLEMENTING",
        )
    return BlockerDecision(blocked=False, reason=None, resume_from_state=None)

