from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from railforge.core.errors import RailForgeError
from railforge.core.models import ContractSpec, TaskItem


class ContractGateError(RailForgeError):
    """Raised when a contract is invalid for the selected task."""


class ContractGate:
    def validate(self, task: TaskItem, contract: ContractSpec) -> ContractSpec:
        errors = []  # type: List[str]

        if contract.task_id != task.id:
            errors.append("task_id_mismatch")
        if not contract.scope:
            errors.append("missing_scope")
        if not contract.allowed_paths:
            errors.append("missing_allowed_paths")
        if not contract.verification:
            errors.append("missing_verification")
        if not contract.rollback:
            errors.append("missing_rollback")
        if not contract.done_definition:
            errors.append("missing_done_definition")
        if not contract.task_context:
            errors.append("missing_task_context")
        if not contract.writeback_requirements.get("required_fields"):
            errors.append("missing_writeback_requirements")
        if "lead_writer" not in contract.role_boundaries:
            errors.append("missing_lead_writer_boundary")
        if "backend_specialist" not in contract.role_boundaries:
            errors.append("missing_backend_specialist_boundary")
        if "frontend_specialist" not in contract.role_boundaries:
            errors.append("missing_frontend_specialist_boundary")
        if "backend_evaluator" not in contract.role_boundaries:
            errors.append("missing_backend_evaluator_boundary")
        if "frontend_evaluator" not in contract.role_boundaries:
            errors.append("missing_frontend_evaluator_boundary")

        unknown_paths = [path for path in contract.allowed_paths if path not in task.allowed_paths]
        if unknown_paths:
            errors.append("allowed_paths_outside_task:%s" % ",".join(unknown_paths))

        if errors:
            raise ContractGateError(", ".join(errors))
        return contract

    def validate_repo_reality(
        self,
        workspace_root: Path,
        contract: ContractSpec,
        task: TaskItem,
    ) -> Optional[str]:
        """校验 allowed_paths 在工作区中实际存在。仅对有 .git 的仓库生效。
        返回 None 表示通过，否则返回错误描述。"""
        if not (workspace_root / ".git").exists():
            return None
        creates_root_list = contract.writeback_requirements.get("creates_root", [])
        missing_roots = []  # type: List[str]
        for path_prefix in contract.allowed_paths:
            target = workspace_root / path_prefix.rstrip("/")
            creates_root = any(
                cr.strip("/") == path_prefix.strip("/")
                for cr in creates_root_list
            )
            if not creates_root and not target.exists():
                missing_roots.append(path_prefix)
        if missing_roots:
            return "repo reality audit failed: paths do not exist in workspace: %s" % ", ".join(missing_roots)
        return None
