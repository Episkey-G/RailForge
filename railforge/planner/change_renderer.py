from __future__ import annotations

from typing import Dict, Iterable, List

from railforge.core.models import ProductSpec, TaskItem


def _bullets(items: Iterable[str], empty: str = "无") -> str:
    values = [item for item in items if item]
    if not values:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in values)


def _decision_bullets(items: Iterable[Dict[str, str]]) -> str:
    lines: List[str] = []
    for item in items:
        topic = item.get("topic") or item.get("prompt") or item.get("id", "未命名决策")
        line = f"- {item.get('id', 'D-XXX')}: {topic}"
        options = item.get("options")
        if options:
            line += f" ({options})"
        lines.append(line)
    if not lines:
        return "- 无"
    return "\n".join(lines)


def render_proposal(
    change_id: str,
    request_text: str,
    spec: ProductSpec,
    questions: List[Dict[str, str]],
    decisions: List[Dict[str, str]],
    result_state: str,
) -> str:
    next_action = "回答 HITL 问题并重新进入规划流程。" if questions else "等待 spec 审批后进入 spec-plan。"
    question_lines = [f"{item['id']}: {item['prompt']}" for item in questions]
    summary = spec.acceptance_criteria or [spec.summary or request_text]
    return (
        "# Proposal\n\n"
        f"## Change\n{change_id}\n\n"
        "## 原始需求\n"
        f"{request_text}\n\n"
        "## 需求摘要\n"
        f"{_bullets(summary)}\n\n"
        "## 约束\n"
        f"{_bullets(spec.constraints)}\n\n"
        "## HITL 问题\n"
        f"{_bullets(question_lines)}\n\n"
        "## 决策点\n"
        f"{_decision_bullets(decisions)}\n\n"
        "## 当前状态\n"
        f"- Run State: {result_state}\n"
        f"- Product Spec Status: {spec.status}\n\n"
        "## 下一步\n"
        f"- {next_action}\n"
    )


def render_design(spec: ProductSpec, tasks: List[TaskItem], decisions: List[Dict[str, str]]) -> str:
    task_summary = [f"{task.id} {task.title}" for task in tasks]
    return (
        "# Design\n\n"
        "## Summary\n"
        f"{spec.summary}\n\n"
        "## Constraints\n"
        f"{_bullets(spec.constraints)}\n\n"
        "## Decision Points\n"
        f"{_decision_bullets(decisions)}\n\n"
        "## Task Strategy\n"
        f"{_bullets(task_summary)}\n\n"
        "## Approval Gates\n"
        "- `spec-research` 未解决问题前不得进入 `spec-plan`\n"
        "- `spec-plan` 产出 backlog draft 后需要 backlog 审批\n"
        "- `spec-impl` 只能消费已审批 backlog\n"
    )


def render_tasks(tasks: List[TaskItem]) -> str:
    lines: List[str] = []
    for task in tasks:
        deps = ", ".join(task.depends_on) if task.depends_on else "none"
        paths = ", ".join(task.allowed_paths)
        verification = " ; ".join(task.verification)
        lines.extend(
            [
                f"- [ ] {task.id} {task.title}",
                f"  - Depends on: {deps}",
                f"  - Allowed Paths: {paths}",
                f"  - Verification: {verification}",
            ]
        )
    return "\n".join(lines)


def render_spec(
    spec: ProductSpec,
    tasks: List[TaskItem],
    questions: List[Dict[str, str]],
    decisions: List[Dict[str, str]],
) -> str:
    requirement_lines: List[str] = []
    for index, task in enumerate(tasks, start=1):
        requirement_lines.extend(
            [
                f"### Requirement {index}: {task.title}",
                _bullets(task.done_definition or [task.title]),
                "",
            ]
        )
    outstanding = [f"{item['id']}: {item['prompt']}" for item in questions]
    return (
        "# Spec\n\n"
        "## Requirements\n"
        f"{chr(10).join(requirement_lines).strip()}\n\n"
        "## Constraints\n"
        f"{_bullets(spec.constraints)}\n\n"
        "## Decision Points\n"
        f"{_decision_bullets(decisions)}\n\n"
        "## Approval Gates\n"
        "- unresolved HITL 问题必须阻塞 `spec-plan`\n"
        "- spec approval required before backlog generation is accepted\n"
        "- backlog approval required before `spec-impl`\n\n"
        "## Outstanding Questions\n"
        f"{_bullets(outstanding)}\n"
    )
