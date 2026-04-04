from __future__ import annotations

from typing import Any, Dict, List, Optional

from railforge.core.models import ContractSpec, ProductSpec, TaskItem

SCHEMA_VERSION = 2


def default_policies() -> Dict[str, Any]:
    return {
        "version": SCHEMA_VERSION,
        "budgets": {
            "default_repair_budget": 2,
            "max_repair_attempts_per_task": 3,
            "require_manual_resume_after_blocked": True,
        },
        "guardrails": {
            "enforce_contract_gate": True,
            "enforce_allowed_paths": True,
            "enforce_verification": True,
        },
    }


def default_models() -> Dict[str, Any]:
    return {
        "version": SCHEMA_VERSION,
        "roles": {
            "lead_writer": {"driver": "hosted_codex", "adapter": "hosted_codex", "model": "gpt-5.4"},
            "backend_specialist": {"driver": "claude_cli", "adapter": "claude_cli", "model": "glm5"},
            "frontend_specialist": {
                "driver": "gemini_cli",
                "adapter": "gemini_cli",
                "model": "gemini-3.1-pro-preview",
            },
            "backend_evaluator": {"driver": "claude_cli", "adapter": "claude_cli", "model": "glm5"},
            "frontend_evaluator": {
                "driver": "gemini_cli",
                "adapter": "gemini_cli",
                "model": "gemini-3.1-pro-preview",
            },
        },
    }


def backlog_payload(project: str, current_task: Optional[str], items: List[TaskItem]) -> Dict[str, Any]:
    return {
        "version": SCHEMA_VERSION,
        "project": project,
        "current_task": current_task,
        "items": [item.to_dict() for item in items],
    }


def render_product_spec_markdown(spec: ProductSpec) -> str:
    assumptions = spec.assumptions or ["无"]
    open_questions = spec.open_questions or ["无"]
    decision_points = spec.decision_points or ["无"]
    return (
        "# Product Spec\n\n"
        "## Status\n%s\n\n"
        "## Summary\n%s\n\n"
        "## Acceptance Criteria\n%s\n\n"
        "## Constraints\n%s\n"
        "## Assumptions\n%s\n\n"
        "## Open Questions\n%s\n\n"
        "## Decision Points\n%s\n"
        % (
            spec.status,
            spec.summary,
            "\n".join("- %s" % item for item in spec.acceptance_criteria),
            "\n".join("- %s" % item for item in spec.constraints),
            "\n".join("- %s" % item for item in assumptions),
            "\n".join("- %s" % item for item in open_questions),
            "\n".join("- %s" % item for item in decision_points),
        )
    )


def render_contract_markdown(contract: ContractSpec) -> str:
    context = contract.task_context or ["无"]
    writeback = contract.writeback_requirements or {}
    required_fields = writeback.get("required_fields", []) or ["无"]
    role_lines = []
    for role, boundary in contract.role_boundaries.items():
        marker = "只读" if boundary.get("read_only") else "可写"
        allowed = boundary.get("allowed_paths", [])
        role_lines.append("- %s: %s" % (role, marker))
        role_lines.extend("  - %s" % item for item in allowed or ["无"])
    return (
        "# Contract - %s\n\n## Scope\n%s\n\n## Non-Scope\n%s\n\n## Allowed Paths\n%s\n\n"
        "## Verification\n%s\n\n## Done Definition\n%s\n\n## Task Context\n%s\n\n"
        "## Writeback\n- result_path: %s\n- required_fields:\n%s\n\n## Role Boundaries\n%s\n\n## Rollback\n%s\n"
        % (
            contract.task_id,
            "\n".join("- %s" % item for item in contract.scope),
            "\n".join("- %s" % item for item in contract.non_scope),
            "\n".join("- %s" % item for item in contract.allowed_paths),
            "\n".join("- %s" % item for item in contract.verification),
            "\n".join("- %s" % item for item in contract.done_definition),
            "\n".join("- %s" % item for item in context),
            writeback.get("result_path", "无"),
            "\n".join("- %s" % item for item in required_fields),
            "\n".join(role_lines or ["- 无"]),
            "\n".join("- %s" % item for item in contract.rollback),
        )
    )
