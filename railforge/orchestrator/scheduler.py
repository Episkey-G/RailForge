from typing import List, Optional

from railforge.core.models import TaskItem
from railforge.planner.task_selector import select_next_task


def select_ready_task(tasks: List[TaskItem]) -> Optional[TaskItem]:
    return select_next_task(tasks)
