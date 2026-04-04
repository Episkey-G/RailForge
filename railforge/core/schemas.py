from __future__ import annotations

from typing import Any, Dict, List, Optional

from railforge.core.models import ContractSpec, ProductSpec, TaskItem

SCHEMA_VERSION = 1


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
            "lead_writer": {"provider": "mock", "mode": "write"},
            "backend_specialist": {"provider": "mock", "mode": "review"},
            "frontend_specialist": {"provider": "mock", "mode": "review"},
            "evaluator": {"provider": "internal", "mode": "judge"},
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
    return (
        "# Product Spec\n\n"
        "## Summary\n%s\n\n"
        "## Acceptance Criteria\n%s\n\n"
        "## Constraints\n%s\n"
        % (
            spec.summary,
            "\n".join("- %s" % item for item in spec.acceptance_criteria),
            "\n".join("- %s" % item for item in spec.constraints),
        )
    )


def render_contract_markdown(contract: ContractSpec) -> str:
    return (
        "# Contract - %s\n\n## Scope\n%s\n\n## Non-Scope\n%s\n\n## Allowed Paths\n%s\n\n"
        "## Verification\n%s\n\n## Rollback\n%s\n"
        % (
            contract.task_id,
            "\n".join("- %s" % item for item in contract.scope),
            "\n".join("- %s" % item for item in contract.non_scope),
            "\n".join("- %s" % item for item in contract.allowed_paths),
            "\n".join("- %s" % item for item in contract.verification),
            "\n".join("- %s" % item for item in contract.rollback),
        )
    )
