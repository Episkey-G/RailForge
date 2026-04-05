from railforge.core.models import AdapterResult
from railforge.planner.clarification_service import ClarificationService


class StubClarificationAdapter:
    def __init__(self, structured):
        self.structured = structured

    def invoke(self, **kwargs):
        return AdapterResult(success=True, summary="ok", metadata={"structured": self.structured})


def _payload(*, can_proceed, open_questions=None, decisions=None, resolved_by_default=None):
    return {
        "enhanced_request": "需求摘要",
        "acceptance_criteria": ["验收条件"],
        "constraints": [],
        "assumptions": [],
        "resolved_by_default": list(resolved_by_default or []),
        "open_questions": list(open_questions or []),
        "decisions": list(decisions or []),
        "can_proceed": can_proceed,
    }


def test_clarification_service_research_blocked() -> None:
    service = ClarificationService(
        StubClarificationAdapter(
            _payload(
                can_proceed=False,
                open_questions=[
                    {
                        "id": "Q-001",
                        "prompt": "请确认业务规则口径。",
                        "category": "clarification",
                        "blocking_reason": "业务规则需要人工确认后才能进入 planning。",
                    }
                ],
            )
        )
    )

    outcome = service.analyze(
        phase="research",
        project="demo",
        request_text="业务口径需要人工确认。",
        answers={},
    )

    assert outcome.can_proceed is False
    assert [item["id"] for item in outcome.unresolved_questions] == ["Q-001"]


def test_clarification_service_planning_blocked() -> None:
    service = ClarificationService(
        StubClarificationAdapter(
            _payload(
                can_proceed=False,
                open_questions=[
                    {
                        "id": "Q-002",
                        "prompt": "请确认最终 API 契约。",
                        "category": "api_contract",
                        "blocking_reason": "未确认契约会阻塞 backlog 分解。",
                    }
                ],
            )
        )
    )

    outcome = service.analyze(
        phase="plan",
        project="demo",
        request_text="规划阶段仍有 API 契约歧义。",
        answers={},
    )

    assert outcome.can_proceed is False
    assert outcome.unresolved_questions[0]["category"] == "api_contract"


def test_clarification_service_treats_marketing_copy_as_non_blocking() -> None:
    service = ClarificationService(
        StubClarificationAdapter(
            _payload(
                can_proceed=True,
                resolved_by_default=["营销 copy 不阻塞 planning"],
            )
        )
    )

    outcome = service.analyze(
        phase="research",
        project="PulseNotch",
        request_text="需要双语营销文案和 Hero copy。",
        answers={},
    )

    assert outcome.can_proceed is True
    assert outcome.unresolved_questions == []


def test_clarification_service_blocks_on_timezone_and_error_copy() -> None:
    service = ClarificationService(
        StubClarificationAdapter(
            _payload(
                can_proceed=False,
                open_questions=[
                    {
                        "id": "Q-002",
                        "prompt": "请确认时区规则。",
                        "category": "timezone",
                        "blocking_reason": "时间口径会影响测试基线。",
                    },
                    {
                        "id": "Q-003",
                        "prompt": "请确认错误提示文案。",
                        "category": "copy",
                        "blocking_reason": "错误提示属于可见 contract。",
                    },
                ],
                decisions=[
                    {
                        "id": "D-001",
                        "topic": "时区规则",
                        "options": "UTC 或业务时区",
                    }
                ],
            )
        )
    )

    outcome = service.analyze(
        phase="research",
        project="todo-app",
        request_text="时区规则和错误提示文案需要人工确认。",
        answers={},
    )

    assert [item["id"] for item in outcome.unresolved_questions] == ["Q-002", "Q-003"]
    assert outcome.decisions[0]["id"] == "D-001"
