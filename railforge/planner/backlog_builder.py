from __future__ import annotations

from typing import List, Tuple

from railforge.core.models import ProductSpec, TaskItem


def _classify_requirement(requirement: str) -> Tuple[str, str, List[str], List[str], str]:
    lowered = requirement.lower()
    if any(token in requirement for token in ["测试", "验证", "回归", "QA"]) or "test" in lowered:
        return ("verification", "补齐验证", ["tests/", ".railforge/tasks/"], ["pytest tests/test_regression.py"], "medium")
    if any(token in requirement for token in ["前端", "页面", "UI", "交互", "文案", "提示"]) or "frontend" in lowered:
        return (
            "frontend",
            "实现前端能力",
            ["frontend/", "tests/"],
            ["pytest tests/test_frontend_flow.py", "playwright ui-review.spec.ts"],
            "high",
        )
    if any(token in requirement for token in ["安装器", "MCP", "文档", "README", "guide", "skill", "命令", "菜单"]):
        return (
            "surface",
            "对齐工作流表面",
            ["installer/", "docs/", ".agents/", "tests/"],
            ["pytest tests/test_installer_flow.py"],
            "medium",
        )
    if any(token in requirement for token in ["恢复", "checkpoint", "LangGraph", "状态机", "contract", "backlog", "planner", "执行器", "评估器"]):
        return ("runtime", "实现运行时能力", ["railforge/", "tests/"], ["pytest tests/test_runtime_planning.py"], "high")
    if any(token in requirement for token in ["后端", "接口", "API", "服务", "校验", "数据库", "权限"]) or "backend" in lowered:
        return ("backend", "实现后端能力", ["backend/", "tests/"], ["pytest tests/test_backend_flow.py"], "high")
    return ("generic", "实现核心能力", ["railforge/", "tests/"], ["pytest tests/test_runtime_planning.py"], "high")


def build_backlog(spec: ProductSpec) -> List[TaskItem]:
    requirements = [item.strip() for item in spec.acceptance_criteria if item.strip()]
    if not requirements:
        requirements = [spec.summary.strip() or "需求满足"]

    classified = [(requirement, _classify_requirement(requirement)) for requirement in requirements]
    explicit_categories = {category for _, (category, *_rest) in classified if category != "generic"}
    if explicit_categories:
        classified = [item for item in classified if item[1][0] != "generic"]
    if not classified:
        classified = [(requirements[0], _classify_requirement(requirements[0]))]

    tasks: List[TaskItem] = []
    previous_ids: List[str] = []
    for index, (requirement, classified_item) in enumerate(classified, start=1):
        _category, prefix, allowed_paths, verification, priority = classified_item
        task_id = f"T-{index:03d}"
        tasks.append(
            TaskItem(
                id=task_id,
                title=f"{prefix}：{requirement}",
                status="ready" if index == 1 else "todo",
                priority=priority,
                depends_on=previous_ids[:],
                allowed_paths=allowed_paths,
                verification=verification,
                repair_budget=2,
                done_definition=[requirement],
            )
        )
        previous_ids.append(task_id)
    return tasks
