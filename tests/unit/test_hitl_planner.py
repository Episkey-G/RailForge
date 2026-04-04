from pathlib import Path

from railforge.adapters.mock import build_default_mock_services
from railforge.artifacts.store import ArtifactStore
from railforge.core.enums import RunState
from railforge.core.models import WorkspaceLayout
from railforge.orchestrator.run_loop import RailForgeHarness


def test_spec_expansion_blocks_for_clarification(tmp_path: Path) -> None:
    harness = RailForgeHarness(workspace=tmp_path, services=build_default_mock_services())

    result = harness.run(project="todo-app", request_text="实现过去日期校验，时区规则和文案需要人工确认。")

    assert result.state == RunState.BLOCKED
    assert result.blocked_reason == "clarification_required"
    store = ArtifactStore(WorkspaceLayout(tmp_path))
    questions = store.load_questions()
    assert questions["unresolved"]


def test_resume_after_answers_blocks_for_spec_approval(tmp_path: Path) -> None:
    harness = RailForgeHarness(workspace=tmp_path, services=build_default_mock_services())
    store = ArtifactStore(WorkspaceLayout(tmp_path))

    blocked = harness.run(project="todo-app", request_text="实现过去日期校验，时区规则和文案需要人工确认。")
    assert blocked.blocked_reason == "clarification_required"

    store.save_answers({"answers": {"Q-001": "按产品说明", "Q-002": "UTC", "Q-003": "日期不能早于今天"}})
    resumed = harness.resume(reason="clarification_resolved", note="已补充规划答案")

    assert resumed.state == RunState.BLOCKED
    assert resumed.blocked_reason == "spec_approval_required"
