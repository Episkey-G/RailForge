from railforge.planner.backlog_builder import build_backlog
from railforge.planner.contract_builder import build_contract
from railforge.planner.spec_expander import expand_request
from railforge.planner.task_selector import select_next_task


def test_spec_expander_extracts_acceptance_criteria() -> None:
    spec = expand_request(
        project="todo-app",
        request_text="用户不能创建过去日期的待办事项。后端接口必须拒绝过去日期。前端需要显示明确错误提示。需要补齐测试。",
    )
    assert spec.title == "todo-app"
    assert len(spec.acceptance_criteria) >= 3
    assert "前端需要显示明确错误提示" in spec.acceptance_criteria


def test_backlog_builder_creates_three_tasks() -> None:
    spec = expand_request(
        project="todo-app",
        request_text="用户不能创建过去日期的待办事项。后端接口必须拒绝过去日期。前端需要显示明确错误提示。需要补齐测试。",
    )
    tasks = build_backlog(spec)
    assert len(tasks) == 3
    assert tasks[0].status == "ready"
    assert tasks[1].depends_on == ["T-001"]
    assert tasks[2].depends_on == ["T-001", "T-002"]


def test_task_selector_picks_first_ready_task() -> None:
    spec = expand_request(project="todo-app", request_text="后端校验、前端提示、测试覆盖")
    tasks = build_backlog(spec)
    selected = select_next_task(tasks)
    assert selected is not None
    assert selected.id == "T-001"


def test_contract_builder_includes_rollback_and_verification() -> None:
    spec = expand_request(project="todo-app", request_text="后端校验、前端提示、测试覆盖")
    task = build_backlog(spec)[0]
    contract = build_contract(task)
    assert contract.task_id == task.id
    assert contract.rollback
    assert contract.verification == task.verification
