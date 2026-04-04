from typing import List

from railforge.core.models import ProductSpec, TaskItem


def build_backlog(spec: ProductSpec) -> List[TaskItem]:
    done_definition = spec.acceptance_criteria[:]
    if not done_definition:
        done_definition = ["需求满足"]

    return [
        TaskItem(
            id="T-001",
            title="Backend validation",
            status="ready",
            priority="high",
            depends_on=[],
            allowed_paths=["backend/", "tests/"],
            verification=["pytest tests/test_due_date.py"],
            repair_budget=2,
            done_definition=done_definition,
        ),
        TaskItem(
            id="T-002",
            title="Frontend feedback",
            status="todo",
            priority="high",
            depends_on=["T-001"],
            allowed_paths=["frontend/", "tests/"],
            verification=["pytest tests/test_due_date.py", "playwright due-date.spec.ts"],
            repair_budget=2,
            done_definition=done_definition,
        ),
        TaskItem(
            id="T-003",
            title="Verification coverage",
            status="todo",
            priority="medium",
            depends_on=["T-001", "T-002"],
            allowed_paths=["tests/", ".railforge/tasks/"],
            verification=["pytest tests/test_due_date.py", "pytest tests/test_regression.py"],
            repair_budget=2,
            done_definition=done_definition,
        ),
    ]

