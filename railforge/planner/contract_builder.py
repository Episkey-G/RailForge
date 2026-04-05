from typing import Optional

from railforge.core.models import ContractSpec, TaskItem
from railforge.planner.planning_contract import PlanningContract, task_scope_mismatches
from railforge.providers.role_profiles import DEFAULT_ROLE_PROFILES


_KNOWN_SURFACES = [
    "railforge/",
    "backend/",
    "frontend/",
    "installer/",
    "docs/",
    ".agents/",
    "tests/",
]


def _task_context(task: TaskItem, planning_contract: Optional[PlanningContract] = None) -> list[str]:
    dependencies = "无" if not task.depends_on else ", ".join(task.depends_on)
    context = [
        f"任务标题：{task.title}",
        f"优先级：{task.priority}",
        f"风险级别：{task.risk_level}",
        f"依赖任务：{dependencies}",
    ]
    if planning_contract and planning_contract.locked_decisions:
        context.extend(f"锁定约束：{item}" for item in planning_contract.locked_decisions)
    if planning_contract and planning_contract.deliverables:
        context.extend(f"规划交付物：{item}" for item in planning_contract.deliverables)
    return context


def _non_scope(task: TaskItem) -> list[str]:
    boundaries = [path for path in _KNOWN_SURFACES if path not in task.allowed_paths]
    items = [f"不修改 {path} 范围内代码" for path in boundaries]
    items.append("不跳过 contract 中声明的验证步骤")
    return items


def _writeback_requirements(task: TaskItem, run_id: str) -> dict[str, object]:
    return {
        "result_path": f".railforge/runtime/execution_results/{run_id}/{task.id}/hosted_codex.json",
        "required_fields": ["task_id", "summary", "changed_files", "verification_notes"],
        "optional_fields": ["follow_up_notes", "blockers"],
        "task_trace_path": f".railforge/runtime/traces/{run_id}/{task.id}/hosted_execution_result.json",
    }


def _role_boundaries(task: TaskItem, run_id: str) -> dict[str, dict[str, object]]:
    task_root = f".railforge/runtime/runs/{run_id}/tasks/{task.id}/"
    review_paths = [
        f".railforge/runtime/reviews/{run_id}/{task.id}/",
        f".railforge/runtime/proposals/{run_id}/{task.id}/",
    ]
    return {
        "lead_writer": {
            "read_only": False,
            "responsibility": "在 allowed_paths 内完成代码实现，并仅向 runtime execution 目录回写协议工件",
            "allowed_paths": list(task.allowed_paths) + [task_root],
            "allowed_tools": list(DEFAULT_ROLE_PROFILES["lead_writer"].allowed_tools),
        },
        "backend_specialist": {
            "read_only": True,
            "responsibility": "提供后端只读审查与补丁建议，只能写 review/proposal 工件",
            "allowed_paths": review_paths,
            "allowed_tools": list(DEFAULT_ROLE_PROFILES["backend_specialist"].allowed_tools),
        },
        "frontend_specialist": {
            "read_only": True,
            "responsibility": "提供前端只读审查与补丁建议，只能写 review/proposal 工件",
            "allowed_paths": review_paths,
            "allowed_tools": list(DEFAULT_ROLE_PROFILES["frontend_specialist"].allowed_tools),
        },
        "backend_evaluator": {
            "read_only": True,
            "responsibility": "提供后端合规评估，只能写 review/proposal 工件",
            "allowed_paths": review_paths,
            "allowed_tools": list(DEFAULT_ROLE_PROFILES["backend_evaluator"].allowed_tools),
        },
        "frontend_evaluator": {
            "read_only": True,
            "responsibility": "提供前端合规评估，只能写 review/proposal 工件",
            "allowed_paths": review_paths,
            "allowed_tools": list(DEFAULT_ROLE_PROFILES["frontend_evaluator"].allowed_tools),
        },
    }


def build_contract(task: TaskItem, planning_contract: Optional[PlanningContract] = None, run_id: str = "active-run") -> ContractSpec:
    scope = [task.title]
    if planning_contract:
        scope.extend(item for item in planning_contract.deliverables if item not in scope)
        mismatches = task_scope_mismatches(task.allowed_paths, planning_contract)
        if mismatches:
            raise ValueError("allowed_paths_outside_planning_contract:%s" % ",".join(mismatches))
    non_scope = _non_scope(task)
    rollback = ["撤回本任务引入的文件变更", "恢复 contract 指定目录到前一稳定状态"]
    done_definition = list(task.done_definition)
    if planning_contract:
        for item in planning_contract.locked_decisions:
            if item not in done_definition:
                done_definition.append(item)
    return ContractSpec(
        task_id=task.id,
        scope=scope,
        non_scope=non_scope,
        allowed_paths=task.allowed_paths,
        verification=task.verification,
        rollback=rollback,
        done_definition=done_definition,
        task_context=_task_context(task, planning_contract=planning_contract),
        writeback_requirements=_writeback_requirements(task, run_id),
        role_boundaries=_role_boundaries(task, run_id),
    )
