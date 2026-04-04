from typing import Dict, List, Optional

from railforge.core.models import TaskItem


_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def _deps_done(task: TaskItem, index: Dict[str, TaskItem]) -> bool:
    for dep in task.depends_on:
        dep_task = index[dep]
        if dep_task.status != "done":
            return False
    return True


def select_next_task(tasks: List[TaskItem]) -> Optional[TaskItem]:
    if not tasks:
        return None
    index = dict((task.id, task) for task in tasks)
    ordered = sorted(
        tasks,
        key=lambda item: (
            _PRIORITY_ORDER.get(item.priority, 99),
            _RISK_ORDER.get(item.risk_level, 99),
            item.id,
        ),
    )

    for task in ordered:
        if task.status == "ready" and _deps_done(task, index):
            return task

    for task in ordered:
        if task.status == "todo" and _deps_done(task, index):
            task.status = "ready"
            return task

    return None

