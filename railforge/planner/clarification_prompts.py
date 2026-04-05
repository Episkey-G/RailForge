from __future__ import annotations

import json
from typing import Any, Dict


_SCHEMA_DESCRIPTION = {
    "enhanced_request": "string, enriched requirement summary for downstream stages",
    "acceptance_criteria": ["list of concrete, testable behaviors"],
    "constraints": ["list of hard or soft constraints discovered from the request and codebase"],
    "assumptions": ["list of explicit assumptions that are safe to carry forward"],
    "resolved_by_default": ["list of details the model decided can proceed without asking the user"],
    "open_questions": [
        {
            "id": "optional stable identifier",
            "prompt": "question shown to the user",
            "category": "clarification|timezone|api_contract|copy|etc",
            "default": "recommended default if user wants to move faster",
            "blocking_reason": "why this blocks planning/execution",
            "source": "what ambiguity or context triggered the question",
        }
    ],
    "decisions": [
        {
            "id": "optional stable identifier",
            "topic": "decision point title",
            "options": "recommended options or comparison frame",
            "source": "which ambiguity or risk this decision comes from",
        }
    ],
    "can_proceed": "boolean, true only when zero blocking ambiguity remains for this phase",
}


def _phase_goal(phase: str) -> str:
    if phase == "plan":
        return "你正在执行 planning ambiguity elimination audit。目标是验证是否还存在任何会阻止零决策规划的歧义。"
    return "你正在执行 research ambiguity discovery。目标是把原始需求增强为约束集，并显式找出必须问用户的阻塞性问题。"


def build_clarification_prompt(*, phase: str, project: str, request_text: str, answers: Dict[str, str], context: Dict[str, Any]) -> str:
    phase_specific = {
        "research": [
            "优先提炼 constraints，而不是做实现设计。",
            "只把真正阻塞 planning 的问题放进 open_questions。",
            "营销文案、品牌文案、页面 copy 不等于前端错误提示文案，除非需求明确指向错误状态。",
        ],
        "plan": [
            "把自己当作 zero-decision 审计器。",
            "只有当实现阶段仍然需要拍板时，才保留 open_questions。",
            "如果所有歧义都能由既有 answers、constraints 或默认假设消解，则 can_proceed 必须为 true。",
        ],
    }
    payload = {
        "project": project,
        "phase": phase,
        "request_text": request_text,
        "captured_answers": answers,
        "context": context,
    }
    return (
        "你是 RailForge 的 clarification analyst，负责按照 CCG 风格执行 prompt/workflow 级 AI 主导澄清。\n"
        f"{_phase_goal(phase)}\n\n"
        "规则：\n"
        "- 问题必须来自真实 ambiguity，而不是词面关键词触发。\n"
        "- 如果一个细节可以安全默认推进，请把它放入 resolved_by_default，而不是强制提问。\n"
        "- 如果没有阻塞性歧义，open_questions 必须为空，can_proceed 必须为 true。\n"
        "- 只输出 JSON 对象，不要输出额外解释。\n\n"
        "输出 JSON schema：\n"
        f"{json.dumps(_SCHEMA_DESCRIPTION, ensure_ascii=False, indent=2)}\n\n"
        "phase-specific guardrails:\n"
        + "\n".join(f"- {item}" for item in phase_specific.get(phase, []))
        + "\n\n上下文：\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )
