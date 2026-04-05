import pytest

from railforge.planner.backlog_builder import build_backlog
from railforge.planner.clarification import analyze_request
from railforge.planner.contract_builder import build_contract
from railforge.planner.planning_contract import PlanningContract
from railforge.planner.spec_expander import expand_request
from railforge.planner.task_selector import select_next_task


def _payload(*criteria: str, can_proceed: bool = True, open_questions=None, decisions=None):
    acceptance = list(criteria) or ["待补充需求"]
    return {
        "enhanced_request": "；".join(acceptance),
        "acceptance_criteria": acceptance,
        "constraints": [],
        "assumptions": [],
        "resolved_by_default": [],
        "open_questions": list(open_questions or []),
        "decisions": list(decisions or []),
        "can_proceed": can_proceed,
    }


def test_spec_expander_extracts_acceptance_criteria() -> None:
    spec = expand_request(
        project="todo-app",
        request_text="用户不能创建过去日期的待办事项。后端接口必须拒绝过去日期。前端需要显示明确错误提示。需要补齐测试。",
        payload=_payload(
            "用户不能创建过去日期的待办事项",
            "后端接口必须拒绝过去日期",
            "前端需要显示明确错误提示",
            "需要补齐测试",
        ),
    )
    assert spec.title == "todo-app"
    assert len(spec.acceptance_criteria) >= 3
    assert "前端需要显示明确错误提示" in spec.acceptance_criteria


def test_backlog_builder_collapses_umbrella_requirement_when_specific_items_exist() -> None:
    spec = expand_request(
        project="todo-app",
        request_text="用户不能创建过去日期的待办事项。后端接口必须拒绝过去日期。前端需要显示明确错误提示。需要补齐测试。",
        payload=_payload(
            "用户不能创建过去日期的待办事项",
            "后端接口必须拒绝过去日期",
            "前端需要显示明确错误提示",
            "需要补齐测试",
        ),
    )
    tasks = build_backlog(spec)
    assert len(tasks) == 3
    assert tasks[0].status == "ready"
    assert tasks[1].depends_on == ["T-001"]
    assert tasks[2].depends_on == ["T-001", "T-002"]


def test_backlog_builder_derives_tasks_from_acceptance_criteria() -> None:
    spec = expand_request(
        project="todo-app",
        request_text="后端校验、前端提示、测试覆盖",
        payload=_payload("后端校验", "前端提示", "测试覆盖"),
    )

    tasks = build_backlog(spec)

    assert [task.title for task in tasks] == [
        "实现后端能力：后端校验",
        "实现前端能力：前端提示",
        "补齐验证：测试覆盖",
    ]
    assert tasks[0].allowed_paths == ["backend/", "tests/"]
    assert tasks[1].allowed_paths == ["frontend/", "tests/"]
    assert tasks[2].allowed_paths == ["tests/", ".railforge/runtime/runs/"]
    assert tasks[0].verification == ["pytest tests/test_backend_flow.py"]
    assert tasks[1].verification == ["pytest tests/test_frontend_flow.py", "playwright ui-review.spec.ts"]
    assert tasks[2].verification == ["pytest tests/test_regression.py"]
    assert tasks[1].depends_on == ["T-001"]
    assert tasks[2].depends_on == ["T-001", "T-002"]


def test_task_selector_picks_first_ready_task() -> None:
    spec = expand_request(
        project="todo-app",
        request_text="后端校验、前端提示、测试覆盖",
        payload=_payload("后端校验", "前端提示", "测试覆盖"),
    )
    tasks = build_backlog(spec)
    selected = select_next_task(tasks)
    assert selected is not None
    assert selected.id == "T-001"


def test_contract_builder_includes_rollback_and_verification() -> None:
    spec = expand_request(
        project="todo-app",
        request_text="后端校验、前端提示、测试覆盖",
        payload=_payload("后端校验", "前端提示", "测试覆盖"),
    )
    task = build_backlog(spec)[0]
    contract = build_contract(task, run_id="run-1")
    assert contract.task_id == task.id
    assert contract.rollback
    assert contract.verification == task.verification


def test_clarification_ignores_marketing_copy_without_error_anchor() -> None:
    result = analyze_request(
        project="PulseNotch",
        request_text="为产品官网编写双语营销文案、Hero copy 和 CTA 文案，保持 clean-room。",
        payload=_payload(
            "为产品官网编写双语营销文案",
            "Hero copy 和 CTA 文案",
            "保持 clean-room",
        ),
    )

    assert not any(item["id"] == "Q-003" for item in result.questions)


def test_backlog_builder_respects_ready_planning_contract_scope() -> None:
    spec = expand_request(
        project="PulseNotch",
        request_text="双语静态站点。共享资源层。",
        payload=_payload("双语静态站点", "共享资源层"),
    )
    planning_contract = PlanningContract(
        status="ready_for_impl",
        allowed_paths=["site/", "openspec/changes/PulseNotch/", "docs/exec-plans/active/"],
        deliverables=[
            "bilingual landing page under site/",
            "shared asset layer under site/assets/",
            "zero-decision OpenSpec artifacts for PulseNotch landing page",
        ],
        locked_decisions=["provider 仅公开 Claude Code / Codex / Gemini CLI", "页面遵守 clean-room 边界"],
    )

    tasks = build_backlog(spec, planning_contract=planning_contract)

    assert [task.title for task in tasks] == [
        "实现前端能力：bilingual landing page under site/",
        "实现前端能力：shared asset layer under site/assets/",
    ]
    assert tasks[0].allowed_paths == ["site/"]
    assert "页面遵守 clean-room 边界" in tasks[0].done_definition
    assert tasks[1].depends_on == ["T-001"]


def test_contract_builder_rejects_scope_outside_planning_contract() -> None:
    spec = expand_request(
        project="todo-app",
        request_text="前端提示",
        payload=_payload("前端提示"),
    )
    task = build_backlog(spec)[0]
    planning_contract = PlanningContract(
        status="ready_for_impl",
        allowed_paths=["site/"],
        deliverables=["site landing page"],
        locked_decisions=[],
    )

    with pytest.raises(ValueError):
        build_contract(task, planning_contract=planning_contract)
