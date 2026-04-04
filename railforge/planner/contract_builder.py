from railforge.core.models import ContractSpec, TaskItem


_KNOWN_SURFACES = [
    "railforge/",
    "backend/",
    "frontend/",
    "installer/",
    "docs/",
    ".agents/",
    "tests/",
]


def _task_context(task: TaskItem) -> list[str]:
    dependencies = "无" if not task.depends_on else ", ".join(task.depends_on)
    return [
        f"任务标题：{task.title}",
        f"优先级：{task.priority}",
        f"风险级别：{task.risk_level}",
        f"依赖任务：{dependencies}",
    ]


def _non_scope(task: TaskItem) -> list[str]:
    boundaries = [path for path in _KNOWN_SURFACES if path not in task.allowed_paths]
    items = [f"不修改 {path} 范围内代码" for path in boundaries]
    items.append("不跳过 contract 中声明的验证步骤")
    return items


def _writeback_requirements(task: TaskItem) -> dict[str, object]:
    return {
        "result_path": ".railforge/runtime/hosted_execution_result.json",
        "required_fields": ["task_id", "summary", "changed_files", "verification_notes"],
        "optional_fields": ["follow_up_notes", "blockers"],
        "task_trace_path": f".railforge/execution/tasks/{task.id}/traces/hosted_execution_result.json",
    }


def _role_boundaries(task: TaskItem) -> dict[str, dict[str, object]]:
    task_root = f".railforge/execution/tasks/{task.id}/"
    review_paths = [f"{task_root}reviews/", f"{task_root}proposals/"]
    return {
        "lead_writer": {
            "read_only": False,
            "responsibility": "在 allowed_paths 内完成代码实现与必要工件回写",
            "allowed_paths": list(task.allowed_paths) + [task_root],
        },
        "backend_specialist": {
            "read_only": True,
            "responsibility": "提供后端只读审查与补丁建议，不直接修改业务代码",
            "allowed_paths": review_paths,
        },
        "frontend_specialist": {
            "read_only": True,
            "responsibility": "提供前端只读审查与补丁建议，不直接修改业务代码",
            "allowed_paths": review_paths,
        },
    }


def build_contract(task: TaskItem) -> ContractSpec:
    scope = [task.title]
    non_scope = _non_scope(task)
    rollback = ["撤回本任务引入的文件变更", "恢复 contract 指定目录到前一稳定状态"]
    return ContractSpec(
        task_id=task.id,
        scope=scope,
        non_scope=non_scope,
        allowed_paths=task.allowed_paths,
        verification=task.verification,
        rollback=rollback,
        done_definition=task.done_definition,
        task_context=_task_context(task),
        writeback_requirements=_writeback_requirements(task),
        role_boundaries=_role_boundaries(task),
    )
