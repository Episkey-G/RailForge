from __future__ import annotations

from typing import List, Optional, Tuple

from railforge.core.models import ProductSpec, TaskItem
from railforge.planner.planning_contract import PlanningContract


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


def _planning_verification(paths: List[str]) -> List[str]:
    if any(path.startswith("site/") or path.startswith("frontend/") for path in paths):
        return ["pytest tests/test_frontend_flow.py"]
    if any(path.startswith("backend/") for path in paths):
        return ["pytest tests/test_backend_flow.py"]
    return ["pytest tests/test_runtime_planning.py"]


def _planning_prefix(paths: List[str]) -> str:
    if any(path.startswith("site/") or path.startswith("frontend/") for path in paths):
        return "实现前端能力"
    if any(path.startswith("backend/") for path in paths):
        return "实现后端能力"
    return "实现核心能力"


def _deliverables_for_scope(deliverables: List[str], paths: List[str]) -> List[str]:
    scoped = []
    for item in deliverables:
        lowered = item.lower()
        if any(path.rstrip("/").lower() in lowered for path in paths):
            scoped.append(item)
    return scoped


def build_backlog(spec: ProductSpec, planning_contract: Optional[PlanningContract] = None) -> List[TaskItem]:
    if planning_contract and planning_contract.is_ready and planning_contract.user_code_paths:
        scoped_deliverables = _deliverables_for_scope(planning_contract.deliverables, planning_contract.user_code_paths)
        requirements = [
            item.strip()
            for item in (scoped_deliverables or spec.acceptance_criteria or [spec.summary.strip() or "需求满足"])
            if item.strip()
        ]
        allowed_paths = planning_contract.user_code_paths
        prefix = _planning_prefix(allowed_paths)
        verification = _planning_verification(allowed_paths)
        constraints = planning_contract.locked_decisions

        tasks: List[TaskItem] = []
        previous_ids: List[str] = []
        for index, requirement in enumerate(requirements, start=1):
            task_id = f"T-{index:03d}"
            done_definition = [requirement]
            for item in constraints:
                if item not in done_definition:
                    done_definition.append(item)
            tasks.append(
                TaskItem(
                    id=task_id,
                    title=f"{prefix}：{requirement}",
                    status="ready" if index == 1 else "todo",
                    priority="high",
                    depends_on=previous_ids[:],
                    allowed_paths=list(allowed_paths),
                    verification=list(verification),
                    repair_budget=2,
                    done_definition=done_definition,
                )
            )
            previous_ids.append(task_id)
        return tasks

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
