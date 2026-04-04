from railforge.core.models import ContractSpec, TaskItem


def build_contract(task: TaskItem) -> ContractSpec:
    scope = [task.title]
    non_scope = ["不修改无关模块", "不跳过验证步骤"]
    rollback = ["撤回本任务引入的文件变更", "恢复 contract 指定目录到前一稳定状态"]
    return ContractSpec(
        task_id=task.id,
        scope=scope,
        non_scope=non_scope,
        allowed_paths=task.allowed_paths,
        verification=task.verification,
        rollback=rollback,
        done_definition=task.done_definition,
    )

