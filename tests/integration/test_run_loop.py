from pathlib import Path

from railforge.adapters.mock import build_default_mock_services, build_repeated_failure_services
from railforge.artifacts.store import ArtifactStore
from railforge.core.enums import RunState
from railforge.core.models import WorkspaceLayout
from railforge.orchestrator.run_loop import RailForgeHarness


def test_run_loop_blocks_for_spec_approval_without_questions(tmp_path: Path) -> None:
    harness = RailForgeHarness(
        workspace=tmp_path,
        services=build_default_mock_services(),
    )

    result = harness.run(project="todo-app", request_text="用户不能创建过去日期的待办事项。后端接口必须拒绝过去日期。前端需要显示明确错误提示。需要补齐测试。")

    assert result.state == RunState.BLOCKED
    assert result.blocked_reason == "spec_approval_required"
    store = ArtifactStore(WorkspaceLayout(tmp_path))
    assert store.load_product_spec().status == "ready_for_approval"


def test_run_loop_blocks_then_resume_completes(tmp_path: Path) -> None:
    services = build_repeated_failure_services()
    harness = RailForgeHarness(workspace=tmp_path, services=services)
    store = ArtifactStore(WorkspaceLayout(tmp_path))

    blocked = harness.run(project="todo-app", request_text="用户不能创建过去日期的待办事项。后端接口必须拒绝过去日期。前端需要显示明确错误提示。需要补齐测试。")
    assert blocked.blocked_reason == "spec_approval_required"

    store.save_approval("spec", approved_by="human", note="spec ok")
    backlog_blocked = harness.resume(reason="spec_approved", note="继续规划")
    assert backlog_blocked.state == RunState.BLOCKED
    assert backlog_blocked.blocked_reason == "backlog_approval_required"

    store.save_approval("backlog", approved_by="human", note="backlog ok")
    blocked = harness.resume(reason="backlog_approved", note="等待 contract approval")
    assert blocked.state == RunState.BLOCKED
    assert blocked.blocked_reason == "contract_approval_required"

    store.save_approval("contract", approved_by="human", note="contract ok")
    blocked = harness.resume(reason="backlog_approved", note="开始执行")
    assert blocked.state == RunState.BLOCKED
    assert blocked.blocked_reason in {"repair_budget_exhausted", "same_failure_signature", "repair_blocked"}

    services.allow_recovery()
    resumed = harness.resume(reason="manual_override", note="人工确认后继续")

    assert resumed.state == RunState.DONE
