from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional

from railforge.core.models import ProductSpec


class ClarificationContractError(ValueError):
    """Raised when AI clarification output does not satisfy the contract."""


@dataclass
class ClarificationQuestion:
    id: str
    prompt: str
    category: str
    default: str = ""
    blocking_reason: str = ""
    source: str = ""

    def to_dict(self) -> Dict[str, str]:
        payload = {
            "id": self.id,
            "prompt": self.prompt,
            "category": self.category,
        }
        if self.default:
            payload["default"] = self.default
        if self.blocking_reason:
            payload["blocking_reason"] = self.blocking_reason
        if self.source:
            payload["source"] = self.source
        return payload


@dataclass
class ClarificationDecision:
    id: str
    topic: str
    options: str = ""
    source: str = ""

    def to_dict(self) -> Dict[str, str]:
        payload = {
            "id": self.id,
            "topic": self.topic,
        }
        if self.options:
            payload["options"] = self.options
        if self.source:
            payload["source"] = self.source
        return payload


@dataclass
class ClarificationOutcome:
    spec: ProductSpec
    questions: List[Dict[str, str]]
    decisions: List[Dict[str, str]]
    answers: Dict[str, str]
    can_proceed: bool
    enhanced_request: str
    resolved_by_default: List[str] = field(default_factory=list)
    trace: Dict[str, Any] = field(default_factory=dict)

    @property
    def unresolved_questions(self) -> List[Dict[str, str]]:
        resolved = set(self.answers)
        return [item for item in self.questions if item["id"] not in resolved]

    @property
    def resolved_questions(self) -> List[Dict[str, str]]:
        return [
            {
                **item,
                "answer": self.answers[item["id"]],
            }
            for item in self.questions
            if item["id"] in self.answers
        ]


def _split_segments(request_text: str) -> List[str]:
    segments = [item.strip() for item in re.split(r"[。！？!?\\.,，、；;\n]+", request_text) if item.strip()]
    if not segments:
        return [request_text.strip() or "待补充需求"]
    return segments


def _as_list(value: Any, field_name: str) -> List[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ClarificationContractError(f"{field_name} must be a list")
    return value


def _as_bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ClarificationContractError(f"{field_name} must be a boolean")


def _require_text(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ClarificationContractError(f"{field_name} must be a non-empty string")
    return value.strip()


def _question_id(prompt: str, category: str, used: set[str], previous_ids: Mapping[str, str]) -> str:
    if prompt in previous_ids:
        return previous_ids[prompt]
    digest = hashlib.sha1(f"{category}:{prompt}".encode("utf-8")).hexdigest()[:6].upper()
    candidate = f"Q-{digest}"
    while candidate in used:
        digest = hashlib.sha1(f"{category}:{prompt}:{len(used)}".encode("utf-8")).hexdigest()[:6].upper()
        candidate = f"Q-{digest}"
    return candidate


def _decision_id(topic: str, used: set[str]) -> str:
    digest = hashlib.sha1(topic.encode("utf-8")).hexdigest()[:6].upper()
    candidate = f"D-{digest}"
    while candidate in used:
        digest = hashlib.sha1(f"{topic}:{len(used)}".encode("utf-8")).hexdigest()[:6].upper()
        candidate = f"D-{digest}"
    return candidate


def _normalize_questions(
    payload: Mapping[str, Any],
    previous_questions: Optional[Mapping[str, Any]],
) -> List[ClarificationQuestion]:
    question_items = _as_list(payload.get("open_questions"), "open_questions")
    previous_prompt_ids = {}
    if previous_questions:
        for bucket in ("questions", "resolved", "unresolved"):
            for item in previous_questions.get(bucket, []) or []:
                if isinstance(item, dict) and item.get("prompt") and item.get("id"):
                    previous_prompt_ids[str(item["prompt"])] = str(item["id"])
    used: set[str] = set(previous_prompt_ids.values())
    questions: List[ClarificationQuestion] = []
    for index, item in enumerate(question_items, start=1):
        if isinstance(item, str):
            prompt = item.strip()
            if not prompt:
                continue
            category = "clarification"
            question_id = _question_id(prompt, category, used, previous_prompt_ids)
            questions.append(ClarificationQuestion(id=question_id, prompt=prompt, category=category))
            used.add(question_id)
            continue
        if not isinstance(item, dict):
            raise ClarificationContractError("open_questions items must be strings or objects")
        prompt = str(item.get("prompt", "")).strip()
        if not prompt:
            raise ClarificationContractError(f"open_questions[{index}] missing prompt")
        category = str(item.get("category") or "clarification").strip() or "clarification"
        question_id = str(item.get("id") or "").strip() or _question_id(prompt, category, used, previous_prompt_ids)
        if question_id in used:
            question_id = _question_id(prompt, category, used, previous_prompt_ids)
        questions.append(
            ClarificationQuestion(
                id=question_id,
                prompt=prompt,
                category=category,
                default=str(item.get("default") or "").strip(),
                blocking_reason=str(item.get("blocking_reason") or "").strip(),
                source=str(item.get("source") or "").strip(),
            )
        )
        used.add(question_id)
    return questions


def _normalize_decisions(payload: Mapping[str, Any]) -> List[ClarificationDecision]:
    decision_items = _as_list(payload.get("decisions"), "decisions")
    used: set[str] = set()
    decisions: List[ClarificationDecision] = []
    for index, item in enumerate(decision_items, start=1):
        if isinstance(item, str):
            topic = item.strip()
            if not topic:
                continue
            decision_id = _decision_id(topic, used)
            decisions.append(ClarificationDecision(id=decision_id, topic=topic))
            used.add(decision_id)
            continue
        if not isinstance(item, dict):
            raise ClarificationContractError("decisions items must be strings or objects")
        topic = str(item.get("topic") or item.get("prompt") or "").strip()
        if not topic:
            raise ClarificationContractError(f"decisions[{index}] missing topic")
        decision_id = str(item.get("id") or "").strip() or _decision_id(topic, used)
        if decision_id in used:
            decision_id = _decision_id(topic, used)
        decisions.append(
            ClarificationDecision(
                id=decision_id,
                topic=topic,
                options=str(item.get("options") or "").strip(),
                source=str(item.get("source") or "").strip(),
            )
        )
        used.add(decision_id)
    return decisions


def _normalize_acceptance(payload: Mapping[str, Any], enhanced_request: str, request_text: str) -> List[str]:
    items = _as_list(payload.get("acceptance_criteria"), "acceptance_criteria")
    criteria = [str(item).strip() for item in items if str(item).strip()]
    if criteria:
        return criteria
    baseline = enhanced_request or request_text
    return _split_segments(baseline)


def analyze_request(
    *,
    project: str,
    request_text: str,
    payload: Mapping[str, Any],
    answers: Optional[Dict[str, str]] = None,
    previous_questions: Optional[Mapping[str, Any]] = None,
) -> ClarificationOutcome:
    answer_map = answers or {}
    enhanced_request = _require_text(payload, "enhanced_request")
    can_proceed = _as_bool(payload.get("can_proceed"), "can_proceed")
    constraints = [str(item).strip() for item in _as_list(payload.get("constraints"), "constraints") if str(item).strip()]
    assumptions = [str(item).strip() for item in _as_list(payload.get("assumptions"), "assumptions") if str(item).strip()]
    resolved_by_default = [
        str(item).strip() for item in _as_list(payload.get("resolved_by_default"), "resolved_by_default") if str(item).strip()
    ]
    questions = _normalize_questions(payload, previous_questions=previous_questions)
    decisions = _normalize_decisions(payload)
    acceptance_criteria = _normalize_acceptance(payload, enhanced_request=enhanced_request, request_text=request_text)

    if not can_proceed and not questions:
        raise ClarificationContractError("can_proceed is false but open_questions is empty")

    all_constraints = [
        "规划阶段遇到歧义必须阻塞并等待人工输入",
        "实现阶段只能在 contract 允许目录内写入",
        "每个任务完成后必须通过双评估器裁决",
    ]
    for item in constraints:
        if item not in all_constraints:
            all_constraints.append(item)

    all_assumptions = [
        "RailForge 使用 Codex 作为 lead writer",
        "每个任务结束后必须经过评估器裁决",
        "文件真源优先于外部 checkpoint",
    ]
    for item in assumptions + resolved_by_default:
        if item not in all_assumptions:
            all_assumptions.append(item)
    if answer_map:
        all_assumptions.extend("%s=%s" % item for item in sorted(answer_map.items()))

    unresolved_prompts = [item.prompt for item in questions if item.id not in answer_map]
    spec = ProductSpec(
        title=project,
        summary=enhanced_request,
        acceptance_criteria=acceptance_criteria,
        constraints=all_constraints,
        assumptions=all_assumptions,
        open_questions=unresolved_prompts,
        decision_points=[item.topic for item in decisions],
        status="draft" if unresolved_prompts or not can_proceed else "ready_for_approval",
        source_request=request_text,
    )
    trace = {
        "enhanced_request": enhanced_request,
        "can_proceed": can_proceed,
        "resolved_by_default": list(resolved_by_default),
        "raw_payload": dict(payload),
    }
    return ClarificationOutcome(
        spec=spec,
        questions=[item.to_dict() for item in questions],
        decisions=[item.to_dict() for item in decisions],
        answers=answer_map,
        can_proceed=can_proceed,
        enhanced_request=enhanced_request,
        resolved_by_default=resolved_by_default,
        trace=trace,
    )
