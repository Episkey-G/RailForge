from railforge.core.enums import RunState
from railforge.core.models import RunMeta, TaskItem
from railforge.guardrails.blocker_detector import detect_blocker
from railforge.guardrails.budgets import repair_decision
from railforge.guardrails.failure_signature import build_failure_signature


def _task() -> TaskItem:
    return TaskItem(
        id="T-001",
        title="Backend validation",
        status="ready",
        priority="high",
        depends_on=[],
        allowed_paths=["backend/", "tests/"],
        verification=["pytest tests/test_demo.py"],
        repair_budget=2,
        done_definition=["reject invalid input"],
    )


def test_failure_signature_is_stable() -> None:
    first = build_failure_signature(
        failed_tests=["tests/test_demo.py::test_rejects_invalid_date"],
        stack_excerpt="AssertionError: expected 400 got 200",
        api_error="POST_/todos_200_instead_of_400",
    )
    second = build_failure_signature(
        failed_tests=["tests/test_demo.py::test_rejects_invalid_date"],
        stack_excerpt="AssertionError: expected 400 got 200",
        api_error="POST_/todos_200_instead_of_400",
    )
    assert first == second


def test_repair_decision_blocks_on_repeated_failure() -> None:
    decision = repair_decision(
        repair_count=2,
        repair_budget=2,
        previous_signature="same",
        current_signature="same",
    )
    assert decision.blocked is True
    assert decision.reason == "repair_budget_exhausted"


def test_blocker_detector_sets_resume_state() -> None:
    run = RunMeta(
        run_id="run-1",
        state=RunState.REPAIRING,
        repair_count=2,
        last_failure_signature="same",
    )
    blocked = detect_blocker(run=run, task=_task(), repeated_failure=True)
    assert blocked.blocked is True
    assert blocked.resume_from_state == "STATIC_REVIEW"
