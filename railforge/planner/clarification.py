from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List

from railforge.core.models import ProductSpec


@dataclass
class ClarificationOutcome:
    spec: ProductSpec
    questions: List[Dict[str, str]]
    decisions: List[Dict[str, str]]
    answers: Dict[str, str]

    @property
    def unresolved_questions(self) -> List[Dict[str, str]]:
        resolved = set(self.answers)
        return [item for item in self.questions if item["id"] not in resolved]


def _split_segments(request_text: str) -> List[str]:
    segments = [item.strip() for item in re.split(r"[。！？!?\\.,，、；;\n]+", request_text) if item.strip()]
    if not segments:
        return [request_text.strip() or "待补充需求"]
    return segments


def _question(question_id: str, prompt: str, category: str) -> Dict[str, str]:
    return {"id": question_id, "prompt": prompt, "category": category}


def analyze_request(project: str, request_text: str, answers: Dict[str, str] | None = None) -> ClarificationOutcome:
    answer_map = answers or {}
    segments = _split_segments(request_text)
    questions: List[Dict[str, str]] = []
    decisions: List[Dict[str, str]] = []

    lowered = request_text.lower()
    if any(token in request_text for token in ["人工确认", "待确认", "待定", "不明确", "不清楚", "需要决策"]):
        questions.append(_question("Q-001", "请确认当前需求中待定项的最终业务口径。", "clarification"))
    if "时区" in request_text and "Q-002" not in answer_map:
        questions.append(_question("Q-002", "请确认日期判断应采用哪个时区。", "timezone"))
        decisions.append({"id": "D-001", "topic": "日期规则时区", "options": "user_local_timezone | server_timezone | utc"})
    if "文案" in request_text and "Q-003" not in answer_map:
        questions.append(_question("Q-003", "请确认前端错误提示文案。", "copy"))
        decisions.append({"id": "D-002", "topic": "错误提示文案", "options": "使用产品提供文案 | 使用临时默认文案"})
    if "api" in lowered and "Q-004" not in answer_map:
        questions.append(_question("Q-004", "请确认接口失败时的响应契约。", "api_contract"))

    assumptions = [
        "RailForge 使用 Codex 作为 lead writer",
        "每个任务结束后必须经过评估器裁决",
        "文件真源优先于外部 checkpoint",
    ]
    if answer_map:
        assumptions.extend("%s=%s" % item for item in sorted(answer_map.items()))

    spec = ProductSpec(
        title=project,
        summary="；".join(segments),
        acceptance_criteria=segments,
        constraints=[
            "规划阶段遇到歧义必须阻塞并等待人工输入",
            "实现阶段只能在 contract 允许目录内写入",
            "每个任务完成后必须通过双评估器裁决",
        ],
        assumptions=assumptions,
        open_questions=[item["prompt"] for item in questions if item["id"] not in answer_map],
        decision_points=[item["topic"] for item in decisions],
        status="draft" if questions else "ready_for_approval",
        source_request=request_text,
    )
    return ClarificationOutcome(spec=spec, questions=questions, decisions=decisions, answers=answer_map)
