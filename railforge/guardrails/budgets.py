from railforge.core.models import RepairDecision


def repair_decision(
    repair_count: int,
    repair_budget: int,
    previous_signature: str,
    current_signature: str,
) -> RepairDecision:
    if repair_count >= repair_budget:
        return RepairDecision(blocked=True, reason="repair_budget_exhausted")
    if previous_signature and previous_signature == current_signature:
        return RepairDecision(blocked=True, reason="repeated_failure_signature")
    return RepairDecision(blocked=False, reason=None)

