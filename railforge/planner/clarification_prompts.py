from __future__ import annotations

import json
from typing import Any, Dict

from railforge.workflow.assets import WorkflowAssetResolver


WORKFLOW_ASSETS = WorkflowAssetResolver()


def build_clarification_prompt(*, phase: str, project: str, request_text: str, answers: Dict[str, str], context: Dict[str, Any]) -> str:
    asset_bundle = WORKFLOW_ASSETS.load_clarification_assets(phase)
    payload = {
        "project": project,
        "phase": phase,
        "request_text": request_text,
        "captured_answers": answers,
        "context": context,
    }
    guardrails = asset_bundle.prompt_contract.get("guardrails", [])
    return (
        f"{asset_bundle.prompt_contract.get('role', '你是 RailForge 的 clarification analyst。')}\n"
        f"{asset_bundle.prompt_contract.get('goal', '')}\n\n"
        "规则：\n"
        + "\n".join(f"- {item}" for item in guardrails)
        + "\n\n"
        "输出 JSON schema：\n"
        f"{json.dumps(asset_bundle.schema, ensure_ascii=False, indent=2)}\n\n"
        "phase contract:\n"
        f"{json.dumps(asset_bundle.phase_contract, ensure_ascii=False, indent=2)}\n\n"
        "boundary reference:\n"
        f"{asset_bundle.boundary_reference}\n\n"
        "question template:\n"
        f"{asset_bundle.question_template}\n\n"
        "上下文：\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )
